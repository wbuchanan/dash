*! dash_parse.mata  v0.1.0
*! Mata utilities for the dash command.
*!
*! Options are parsed by Stata's -syntax-, where dash.ado declares twoway's
*! options with twoway's minimum abbreviations; nothing here rewrites an
*! option word.  This library reads by value what must not be parsed as
*! Stata code, and checks what -syntax- cannot:
*!   1. character-level helpers: JSON escaping, a program's arguments read
*!      by value, UTF-8 validation, user text echoed as text, a saving()
*!      path, a KPI's percentile, a layout() grid;
*!   2. plot types: twoway's abbreviations, the types dash refuses by name,
*!      and the immediate values of scatteri, pci and pcarrowi;
*!   3. the command line split into plot segments, at || or (), and the
*!      comma that starts the options;
*!   4. the variables a spec names, in its plots and in its qualifiers;
*!   5. filter(), link() and the registry, and the option names a segment
*!      holds.
*!
*! Public API: the functions dash.ado calls, which are the list
*! _dash_require_mata checks (`_needed' in dash.ado).  Every other function
*! here is reached from these, call by call.  test/test_file_headers.py
*! holds this list to `_needed', and test/test_no_orphans.py holds every
*! function to a caller.
*!
*!   _dash_json_escape(s)
*!       s escaped for a JSON string: the backslash, the double quote and
*!       every byte below 0x20, and the backtick, dollar sign and
*!       apostrophe written as JSON escapes (backslash u 0060, 0024 and
*!       0027), so the result can be expanded inside compound quotes.
*!
*!   _dash_dp_format(fmt)
*!       fmt with its decimal point a comma when c(dp) is "comma" and fmt
*!       is a numeric %w.df/g/e[c] format (WP-31 G2): display %9.2f under
*!       set dp comma prints as %9,2f does.  Any other format unchanged.
*!
*!   _dash_json_str_args()
*!       dash.ado's _dash_json_str: its `0' read by value, the text
*!       JSON-escaped into the local _dash_jsv, the name into _dash_jsn.
*!
*!   _dash_scheme_dirs_json()
*!       The ado-path as Stata's findfile walks it, a JSON array of at most
*!       64 directories (WP-30 P1.25b): "." is c(pwd), a relative entry is
*!       joined to it, ~ entries are kept as written, and an entry holding
*!       a backtick, dollar sign, double quote or control character is
*!       skipped.
*!
*!   _dash_text_args(nlead, ntail, optnum)
*!       A program's `0' read by value: its first nlead and last ntail
*!       arguments (dash's own words) into _dash_a1, _dash_a2, ..., their
*!       count into _dash_na, and the one user text between them, less one
*!       pair of enclosing quotes, into _dash_txt.  With optnum, a last
*!       argument that is all digits is taken as one more.
*!
*!   _dash_path_badchar(path)
*!       The byte value of the first character saving() refuses in path --
*!       the double quote, backtick, dollar sign or a control character
*!       (1-31, 127) -- or 0.
*!
*!   _dash_prefix_word()
*!       The caller's first word into _pf_word when it is one of twoway's own
*!       command words (twoway tw two twow twowa graph gr gra grap, any
*!       case), else "": dash replaces twoway, so dash.ado refuses it.
*!
*!   _dash_saving_parse(s, ext)
*!       saving()'s one grammar, as twoway reads it; refuses r(198) or sets
*!       _sv_file, _sv_replace, _sv_asis, _sv_gph, _sv_comma and _sv_img.  Its
*!       internal helper is _dash_saving_split().
*!
*!   _dash_seg_saving(seg)
*!       The value of the last saving() an option list gives, as typed.
*!
*!   _dash_play_find(name, personal)
*!       The recording file twoway's play() reads, or "".
*!
*!   _dash_grec_ok(path)
*!       1 when a file starts with a Graph Recorder header.
*!
*!   _dash_launch_quote(path, os)
*!       path quoted for the To launch: line: single quotes on a Mac and
*!       Unix, double quotes on Windows.
*!
*!   _dash_launch_warn(path, os)
*!       On Windows, the line naming % and ! in path; else "".
*!
*!   _dash_abs_path(path, pwd, os)
*!       path when it is absolute on os, else pwd, one separator and path,
*!       with nothing normalised.
*!
*!   _dash_graph_names(list, max)
*!       The first max graph names of list, then "and N more".
*!
*!   _dash_cmd_metachar(path)
*!       The byte value of the first character Windows' command shell
*!       reads in a quoted path -- % ! ^ & | < > ; -- or 0.
*!
*!   _dash_check_utf8(s)
*!       Refuses s, r(198), unless it is well-formed UTF-8.
*!
*!   _dash_say(style, before, value, after)
*!       Print before + value + after as one line in SMCL style "err",
*!       "txt" or "res", every character shown as written.
*!
*!   _dash_pyname()
*!       The Python dash names in its messages: c(python_exec) when set,
*!       else "the Python Stata found, " + the caller's local _dd_x.
*!
*!   _dash_note(before, value, after)
*!       Print before + value + after as one note, (note:  ...), in text
*!       colour on Stata's error channel, as twoway prints its notes.
*!
*!   _dash_opt_tokens(s)
*!       The top-level options of an option text, as typed: split at
*!       blanks outside parentheses, "quotes" and compound quotes (WP-31
*!       B4b, read by dash.ado's _dash_contour_split).
*!
*!   _dash_dashonly_typed(text, inp)
*!       "<row>|<index>|<hint>|<name>|<word>" for the first spelling of
*!       text that twoway refuses and dash once took (WP-35 DT-15), or "".
*!
*!   _dash_dashonly_say(hit, toks)
*!       Refuses that hit as twoway refuses it, then names twoway's
*!       spelling (P4-9); r(198).
*!
*!   _dash_omit_pair(opts, ptypes)
*!       twoway's message word for two omit options in one command
*!       (omitanymissomitallmiss), "" when it takes them (WP-35
*!       basic:PT-8).
*!
*!   _dash_maxaxes_val(text, opt)
*!       The value of the last maxaxes(), yaxis() or xaxis() in an option
*!       text, "" when absent; with opt "drop", the text less its
*!       maxaxes() copies (WP-35 GW-3).
*!
*!   _dash_rightmost_keep(names, flags)
*!       1 for each option token kept, 0 for an earlier copy of a valued
*!       option twoway takes rightmost; flags keep every copy (WP-35 MS-1).
*!
*!   _dash_pcycle_bad(plots, p)
*!       1 when pcycle(p) leaves a series of the plots JSON no whole p#,
*!       as twoway refuses it "option seriesid() not allowed" (WP-31 C8d).
*!
*!   _dash_colorrule_check(t)
*!       colorrule()'s text as twoway reads it: the caller's local _crc
*!       "" (drawn), "spec" (an invalid % or * part) or "rule" (a rule twoway
*!       has no style for, named in the local _crn); _crf the value with
*!       an abbreviated rule written in full.
*!
*!   _dash_mlabff_refusal(unk, graph)
*!       The error twoway gives for mlabfontface() among the catch-all
*!       options unk (graph 1: after the paren-mode comma), in the
*!       caller's locals _mf_on, _mf_rc and _mf_msg (MLF-01).
*!
*!   _dash_mlabff_strip(s)
*!       The option text s without its empty mlabfontface() copies.
*!
*!   _dash_is_digits(s, maxlen)
*!       1 when s is 1..maxlen ASCII digits and nothing else.
*!
*!   _dash_kpi_pctile(stat, numname, whyname)
*!       A KPI statistic read as a percentile, p#: why it is or is not one
*!       into the local whyname, and its number into numname.
*!
*!   _dash_layout_cells(layout)
*!       Cells an explicit layout() grid asks for, or missing.
*!
*!   _dash_layout_refusal(layout, registry)
*!       "" when dash build can draw layout() as written, else the refusal.
*!
*!   _dash_bare_string_refusal(cmd)
*!       twoway's refusal of a quoted string standing alone among the
*!       options, or "" (WP-31 D16b).
*!
*!   _dash_stray_quote_refusal(cmd)
*!       twoway's refusal of option text holding a stray "', as
*!       "<rc>|<first line>", or "" (WP-43 LT-24).
*!
*!   _dash_legend_first_refusal(text)
*!       twoway's refusal of a legend() word before top/bottom/left/right,
*!       or "" (WP-31 D16).
*!
*!   _dash_tabs_unwrap(tabs)
*!       tabs() less one pair of quotes around the whole value (WP-31 D14).
*!
*!   _dash_tabs_refusal(tabs, registry)
*!       "" when every tabs() name is registered and every per-tab layout()
*!       reads whole, else the refusal (WP-31 D14).
*!
*!   _dash_axlabel_refusal(text)
*!       The part of an axis label value twoway refuses, or "" (WP-31 D6).
*!
*!   _dash_axlabel_runs(text)
*!       An axis label value's runs of values, for numlist (WP-44 DG-9).
*!
*!   _dash_axlabel_custom_refusal(text)
*!       twoway's line for custom with an edit and no values, or "" (WP-44 AX-5).
*!
*!   _dash_expand_plottype(abbrev, out_macro)
*!       The plot type abbrev names, abbreviated as twoway allows, into
*!       out_macro; "" when it names no type dash draws.
*!
*!   _dash_kernel_full(word)
*!       The full kernel name, lower case, for a word twoway's kernel()
*!       takes (gau is gaussian, ep and epan epanechnikov); any other
*!       word as given, for the kernel rule to refuse.
*!
*!   _dash_fn_points_json(yvar, n, x0, dx[, dropxy])
*!       A function layer's points as the JSON object
*!       {"x0":..,"dx":..,"y":[..]}: x0 and dx the generator's r(min) and
*!       r(delta), y the first n values of yvar, each %24.17g, a missing
*!       value null.
*!
*!   _dash_fit_points_json(nobs)
*!       A fit layer's points (WP-31 C4) from the serset in memory:
*!       {"x":[..],"y":[..],"lo":[..],"hi":[..],"nobs":n}, the limits only
*!       when the serset has them, each %24.17g, a missing value null.
*!
*!   _dash_fit_panel_key(vars, gvar, gi)
*!       The by() values of group gi of gvar as a JSON list (WP-37
*!       stat:PT-12): a number %24.17g; a string, or a missing number's
*!       code text (".", ".a" .. ".z"), as {"s":[<its bytes>]}.
*!
*!   _dash_fit_panel_add(sc, key, pts)
*!       Appends {"key":key,"points":pts} to the string scalar named sc,
*!       a comma before every entry but the first (WP-37 stat:PT-12).
*!
*!   _dash_fit_opt_bad(s)
*!       1 when estopts()/predopts()/estcmd() text holds a semicolon,
*!       backtick, dollar sign, line break, odd double quote or stray
*!       compound close (WP-31 C4).
*!
*!   _dash_recast_canon(name, spellings)
*!       The full plot-type name name spells among "full:minimum ..."
*!       spellings, or "" (WP-31 C4, fitplot() and ciplot()).
*!
*!   _dash_unbound_cands(raw, cap)
*!       The options of a parser's catch-all whose value -syntax- may not
*!       have bound, into the caller's locals _ru_n, _ru_tok<i>, _ru_nm<i>
*!       and _ru_rc<i> (twoway's code for each, r(109) or r(198)).
*!
*!   _dash_fn_stray_close(s)
*!       1 when s holds a compound-quote close "' with no open before it,
*!       which twoway's parse refuses in a function expression, r(198).
*!
*!   _dash_fn_spec_tail(path, names, sc)
*!       Closes the spec file at path, whose last "}" was left off, with
*!       ,"function_points":{..}} -- the string scalar sc's points as the
*!       one-line graph's, or each named graph's point file -- or a
*!       bare "}" when there are none; points that are not dash's are
*!       skipped with a note.
*!
*!   _dash_fpts_path(name)
*!       The path of graph name's point file, fp-<hex of name>.txt in the
*!       session's points folder $dash__fpdir, or "" (WP-36 plat:PT-4).
*!
*!   _dash_fpts_put(name, text)
*!       Replaces the contents of name's point file, when it exists.
*!
*!   _dash_fpts_drop(name)
*!       Removes name's point file; none is no error.
*!
*!   _dash_fpts_clear()
*!       Removes every point file of the session's points folder.
*!
*!   _dash_by_scan(scname)
*!       twoway's three by() parse stages over the tail in the string
*!       scalar scname (WP-30 P1.15b): the first copies of rows(), cols(),
*!       holes(), iscale() and imargin(), whether each may go to -syntax-,
*!       and the first leftover word in typed order, into _byg_* locals.
*!
*!   _dash_by_shrinks(tail)
*!       1 when the by() tail holds a shrink or overallshrink word, matched
*!       by _dash_by_grammar() as _dash_by_scan matches it (WP-41 BY-5:
*!       twoway refuses aspect() beside it); a word inside a sub-option's
*!       text is not one.
*!
*!   _dash_by_clamp(scname, limit)
*!       Rewrites, in the tail held by the string scalar scname, the first
*!       copy of rows() or cols() above limit to limit (the by_groups
*!       limit), and names the options changed in the local _byg_clamped.
*!
*!   _dash_legend_pos_text(scname)
*!       The first position() text of by()'s legend(), clegend(), plegend()
*!       or *loc() copies, in the tail held by the string scalar scname,
*!       that is not a clock position 0-12 as typed; "" when none (WP-41
*!       BY-7: twoway's clockdir note).
*!
*!   _dash_by_plegend_at(scname)
*!       1 when the first plegend() of the by() text held by the string
*!       scalar scname names at(#) with # >= 1, else 0 (WP-41 K10:
*!       twoway's r(4019) under coloruseplegend).
*!
*!   _dash_rep_scan(opts, unk, cap)
*!       Whether an option list may give an option twice, and its distinct
*!       spellings, into the caller's locals _rp_go, _rp_n, _rp_nm<i> and
*!       _rp_tok<i>.
*!
*!   _dash_hz_order(opts)
*!       The words spelling horizontal and vertical, each flag's first
*!       spelling, in the order typed: "vert hor", one word or ""
*!       (WP-30 P1.9a).
*!
*!   _dash_rep_keyof(snames)
*!       The option a word read alone set, from the parser's s() names.
*!
*!   _dash_rep_reduce(opts, ptype)
*!       The option list with one copy of each option, as twoway reads a
*!       repeated one (the last copy, the first for p(), or the copies
*!       merged); the caller's local _rp_refuse names a unique option
*!       given twice.
*!
*!   _dash_scale_untransformable(v)
*!       1 when the last transform word of a merged scale value is atanh,
*!       logit or log1m, which twoway's graph fails on (WP-44 AX-9, D75).
*!
*!   _dash_stylelist_keys()
*!       The style options read as stylelists across an expanded varlist.
*!
*!   _dash_tw_value_msg(opt, ptype, cls, value)
*!       twoway's "<rc>|<first line>" for a value of class cls it refuses
*!       in option opt on plot type ptype (_dash_tw_value_tab), or "".
*!
*!   _dash_p_take(opts)
*!       opts less its p1() .. p20() words, each kept in the caller's
*!       locals _pt_n and _pt_pairs; _pt_bad the first above p20().
*!
*!   _dash_p_seg(opts, ptype, n)
*!       A plot's options with its own p<j>() and the graph's p<k>() for
*!       it applied, as twoway applies them; _pa_named the words not drawn.
*!
*!   _dash_p_unknown(unk, ptype)
*!       Refuses the options of p#() values twoway does not take, in its
*!       words.
*!
*!   _dash_stylelist_norm(raw)
*!       "" when a style value holds only empty quotes; else raw unchanged.
*!
*!   _dash_stylelist_pick(raw, i)
*!       The stylelist element the i-th y takes ("" for the default), with
*!       twoway's . = .. ... and padding.  Helper _dash_stylelist_elems.
*!
*!   _dash_stylelist_bad(raw)
*!       1 when a .. or ... of a stylelist is not its last element.
*!
*!   _dash_stylelist_paren(raw)
*!       twoway's "( red )" for the first element opening with "(", or "".
*!
*!   _dash_stylelist_eqlead(raw)
*!       The first bare element led by a glued "=" (=blue), or "".
*!
*!   _dash_subopt_colour_comma(value)
*!       twoway's "invalid '<w>'" for a comma colour inside a structured
*!       option's value, or "".
*!
*!   _dash_colour_comma(v)
*!       The word of twoway's "invalid '<w>'" for one colour written
*!       with commas, or "" when twoway draws it.
*!
*!   _dash_stylelist_blank(raw, n)
*!       The first quoted blank element among the n used ones, or 0.
*!
*!   _dash_stylelist_blank_words(key)
*!       twoway's line refusing a used blank element of option key, or "".
*!
*!   _dash_stylelist_probe(tok)
*!       name(x) for an option word whose value is only empty quotes.
*!
*!   _dash_stylelist_locals(raw, stub)
*!       A stylelist's elements as the caller's locals <stub>n, t<j>, q<j>.
*!
*!   _dash_varlabel_tail(raw, i)
*!       yvarlabel()'s words from the i-th on, as typed (WP-31 D8).
*!
*!   _dash_connect_canon(kind, e)
*!       One connect() or cmissing() element as twoway reads it: the
*!       canonical style name, y or n; "" when empty, "?" when unknown.
*!
*!   _dash_rep_und_scan(opts, ptype)
*!       An option dash does not declare, given twice where twoway takes
*!       it once (_dash_rep_und_tab), into the caller's local _rp_refuse;
*!       the graph-wide ones the list gives into its local _rp_gund.
*!
*!   _dash_rep_und_cross(acc, add)
*!       The graph-wide ones of one more option list against the lists
*!       before it; the caller's local _rp_refuse names a second copy.
*!
*!   _dash_log_split(src, out)
*!       The plot parser's option text without the words log and nolog
*!       (twoway's graph option logging), those words into local out.
*!
*!   _dash_logit_typed(opts)
*!       The first word spelling lowess's logit or its off form, as typed.
*!
*!   _dash_barwidth_typed(opts)
*!       The first word spelling barwidth() as typed (refused on rcap and rcapsym).
*!
*!   _dash_foreign_scan(opts, ptype, unk, graph)
*!       The option words of a list, for dash.ado to find one twoway
*!       refuses even once: in upper case, or a plot option after the
*!       paren-mode comma; into the caller's locals _fs_go, _fs_n, ...
*!
*!   _dash_unknown_scan(opts, unk, ptype, graph)
*!       The option words of a list in order, classed for dash.ado's
*!       _dash_refuse_unknown; into the caller's locals _uk_go, _uk_n, ...
*!
*!   _dash_rep_prefix(opts, n)
*!       The first n option words of opts, as typed.
*!
*!   _dash_opt_typed(opts, canon, table)
*!       The option of opts that canon names, as typed ("ba()" for
*!       bands()), for a refusal's first line; canon when none is.
*!
*!   _dash_silent_drop(p, ptype)
*!       The pending names less those twoway draws nothing of on ptype.
*!
*!   _dash_pending_note(p)
*!       The pending names as the note writes them, "()" after a valued one.
*!
*!   _dash_valued_names(raw)
*!       The option names of raw typed with a value.
*!
*!   _dash_kernel_clash(opts, ptype)
*!       "one" for two kernel options, "old" for one beside kernel(), as
*!       twoway refuses them on lpoly, lpolyci and kdensity; else "".
*!
*!   _dash_kernel_flag(unk, ptype)
*!       A kernel written as an option of its own (gau, epan2 ...) on
*!       lpoly, lpolyci or kdensity, read as kernel(<name>): the full
*!       name into the caller's local _kf_name, unk less it into _kf_rest.
*!
*!   _dash_rep_optname(tok)
*!       The name an option word was typed with, or "" when the word is
*!       not an option.
*!
*!   _dash_zyx_abbrev(unk, raw)
*!       contour's i() .. inter() and colorl .. colorline, which the plot
*!       parser leaves to its catch-all unk, read as interp() and
*!       colorlines: _za_iset, _za_interp, _za_cl and _za_rest (unk less
*!       them) into the caller's locals.
*!
*!   _dash_bcal_json(cal, lo, hi)
*!       A business calendar's days lo..hi, {"min":lo,"td":[...]}, read by
*!       dofb() at registration (WP-31 G7).
*!
*!   _dash_fn_panel_count(byraw, touse)
*!       The panels by() draws over the rows touse marks, for the function
*!       layers evaluated once per panel (WP-31 C12).
*!
*!   _dash_range_panel(rp, p)
*!       The p-th "lo hi" pair of a range_panels string, for range(varname)
*!       per by() panel (WP-41 BY-27).
*!
*!   _dash_lpolyci_opts(unk, ptype)
*!       lpolyci's pwidth() and var() taken out of the catch-all by value,
*!       and twoway's checks on them and on level(), in twoway's order:
*!       the caller's locals _lpo_pwidth, _lpo_var, _lpo_rest, _lpo_rc,
*!       _lpo_msg (WP-29 P0.9).  Helpers _dash_lpo_onenum, _dash_lpo_isint.
*!
*!   _dash_rep_merge_locals(key, m1, m2, out)
*!       Two copies of option key, the caller's locals m1 then m2, merged
*!       as twoway merges them, into the caller's local out; two region
*!       copies through _dash_rep_region, each copy editing the last as
*!       twoway's region parser applies them, every margin() kept (WP-30
*!       P1.20a).
*!
*!   _dash_at_parse(raw, datesok)
*!       Every text() or ttext() copy of raw (cut at char(30) outside
*!       quotes and tokenised in one pass by _dash_at_lex) read as twoway
*!       reads it: points through _dash_at_isnum, lines unquoted by
*!       _dash_at_unq, into the caller's _at_* locals (WP-30 P1.10).
*!
*!   _dash_at_globals(s [, ev])
*!       s with each $name, ${name} and $$name replaced by the global's
*!       value (WP-31 D13); with ev 1 its =exp runs evaluated by the safe
*!       evaluator (WP-43 LT-20, P4-6, P4-7; helpers _dash_at_exp_runs,
*!       _dash_at_exp, _dash_at_xp, _dash_at_xf, _dash_at_xws): numbers,
*!       strings, operators and the whitelisted functions computed in
*!       Mata, never by Stata; anything else kept as written.  dash.ado
*!       applies it to the graph's text options (D13b) and _dash_at_parse
*!       to each text() line, both with ev 1.
*!
*!   _dash_at_isnum(tok)
*!       1 when tok is a number as twoway's numlist reads it (WP-30
*!       P1.10); dash.ado's text() quote check reads points through it.
*!
*!   _dash_gt_qadded(s [, ev])
*!   _dash_gt_qtexts(raw)
*!       The option text before its options (helper _dash_gt_qleft); its
*!       globals expanded when they add a double quote, which dash.ado
*!       refuses as twoway does in text(), ttext() and tick labels
*!       (WP-31 D13b).
*!
*!   _dash_gt_ccl(s)
*!       s with each {ccl name} replaced by c(name) as twoway's graph text
*!       draws it (WP-31 E9); applied by dash.ado to the graph's text
*!       options and by _dash_at_parse to each text() line.
*!
*!   _dash_at_dates(u1, u2)
*!       ttext()'s date literals converted in their x axis's unit by
*!       _dash_tdate_value, or 198 and the token in _at_err.
*!
*!   _dash_at_place(p)
*!       twoway's compass direction for placement(p), "" for a name twoway
*!       notes.
*!
*!   _dash_at_orient(o)
*!       twoway's orientation for orientation(o), "" for a name it notes.
*!
*!   _dash_style_word(cls, w)
*!       The canonical name style class cls (compass2dir, tb_orientstyle,
*!       clockdir, gridringstyle, anglestyle, connectstyle) reads the word
*!       w as, by the class's _unabbrev rule; "" for a word it notes.
*!
*!   _dash_edge_span(pre)
*!       twoway's refusal of span or nospan on an edge title, in the
*!       caller's local _es_msg (WP-31 D2b).
*!
*!   _dash_at_canon()
*!       One copy's drawn sub-options from the caller's syntax locals, in
*!       full names, JSON-escaped.
*!
*!   _dash_at_copy(k)
*!       Copy k of the last parse into the caller's locals _at_o, _at_s
*!       and _at_e.
*!
*!   _dash_at_records(kind)
*!       The last parse's records as _dash_at_json() objects, comma-joined,
*!       into the caller's local _at_json.
*!
*!   _dash_json_first_num(s, key)
*!       The first "key":"<digits>" value in s, or missing: a graph's
*!       added_text_n, summed over a dashboard (WP-30 P1.10).
*!
*!   _dash_immediate(vals, w)
*!       Read the immediate values of scatteri (w = 2) or of pci and
*!       pcarrowi (w = 4) as twoway reads them, into the caller's locals
*!       _pci_json, _pci_err, _pci_bad, _pci_left, _pci_hasleft,
*!       _pci_stop, _pci_n, _pci_nlab.
*!
*!   _dash_comma_pos(input, out_macro)
*!       Position (1-based) of the first comma outside quotes and
*!       parentheses, or "0", into out_macro.
*!
*!   _dash_split_segs(input [, allow_empty])
*!       Split the raw command line into plot segments, into the caller's
*!       locals _n_segs, _seg_1 .. _seg_N (each with its plot type),
*!       _graph_opts_raw and _graph_qual_raw.  allow_empty 1 (_dash_plot's
*!       call: bare dash is bare twoway) takes no plot as zero segments.
*!
*!   _dash_extract_vars(json_str, out_macro)
*!       The variables the plots of a spec name, blank-separated, into
*!       out_macro.
*!
*!   _dash_extract_hover_vars(json_str, out_macro, bad_macro, why_macro)
*!       The variables a graph's hover() names, each once and checked, into
*!       out_macro; the first word that is not one into bad_macro, with
*!       why_macro "name" or "var" (WP-29 P0.10).
*!
*!   _dash_extract_qual_vars(json_str, out_macro)
*!       The names a spec's "by" and "if_expr" hold, each once, into
*!       out_macro.
*!
*!   _dash_qual_expand(s)
*!       The if-expression s with each variable it abbreviates written out.
*!
*!   _dash_qual_reset()
*!       Empty the table of distinct qualifiers one export evaluates.
*!
*!   _dash_qual_rewrite(json, errmacro, name_them)
*!       A graph's JSON with each if_expr/in_expr pair replaced by the
*!       __dashq<k> column that holds it; "" and the reason in errmacro
*!       when a pair cannot be evaluated.
*!
*!   _dash_qual_take(ifx, inx, errmacro, name_them)
*!       The __dashq<k> column that holds a KPI's if and in, "" for none;
*!       the reason in errmacro when they cannot be evaluated.
*!
*!   _dash_qual_export()
*!       The distinct qualifiers, into the caller's locals _dq_n, _dq_if_k,
*!       _dq_in_k and _dq_by_k.
*!
*!   _dash_qual_orders()
*!       The distinct by() orders of that table, into the caller's locals
*!       _dq_nord and _dq_ord_j.
*!
*!   _dash_reserved_prefix(names)
*!       The prefix an export names its working columns with: __dash, or
*!       the first __dsh<k>_ no name of names starts with (WP-35 DT-19).
*!
*!   _dash_esample_sub(s, nm)
*!       The expression s with each e(sample) outside its literals read as
*!       the variable nm, the export's copy of e(sample) (WP-35 DT-19).
*!
*!   _dash_expr_words(s)
*!       The words of the expression s outside its literals that could
*!       name a variable, each once (WP-35 DT-19).
*!
*!   _dash_sort_reset()
*!       Empty the join-order table (sort(varlist)'s rank columns).
*!
*!   _dash_sort_scan(json)
*!       Every "sortvars" value of json into that table, once each; the
*!       caller's _ds_bad set to the first value that is not names.
*!
*!   _dash_sort_export()
*!       The table into the caller's locals _ds_n and _ds_v<k>.
*!
*!   _dash_tsop_reset()
*!       Empty the time-series table (plot-variable operator columns).
*!
*!   _dash_tsop_canon(expr)
*!       1 when expr is <operators>.<exact variable name>, else 0.
*!
*!   _dash_tsop_rewrite(json, errmacro)
*!       json with each operated plot variable replaced by its column
*!       __dasht<k>; the reason in errmacro for one that is not canonical.
*!
*!   _dash_tsop_export()
*!       The table into the caller's locals _dts_n and _dts_e<k>.
*!
*!   _dash_tsop_meta(fmtmacro)
*!       The spec's "ts_cols" object (the weight columns' entries too);
*!       the columns' formats merged into the caller's local fmtmacro.
*!
*!   _dash_wexp_ok(expr)
*!       1 when a weight expression may reach generate (no backtick, $,
*!       quote, ;, tab or line break; 512 bytes).
*!
*!   _dash_wexp_reset()
*!       Empty the weight-expression table.
*!
*!   _dash_wexp_rewrite(json, errmacro)
*!       json with each weight expression replaced by its column
*!       __dashw<k>; the reason in errmacro for one that may not be run.
*!
*!   _dash_wexp_export()
*!       The table into the caller's locals _dwx_n and _dwx_e<k>.
*!
*!   _dash_frame_set(f)
*!       The frame the table entries made next belong to (WP-33 33-07).
*!
*!   _dash_frame_set_all(on)
*!       1: every qualifier pair, the empty one too, takes a column.
*!
*!   _dash_frames_reset()
*!       Empty the build's frame records (keep lists, splits, label sets).
*!
*!   _dash_frames_keep_add(f, g, vars)
*!       vars into frame f's keep list, and graph g's own list.
*!
*!   _dash_frames_keep_of(f)
*!       Frame f's keep list.
*!
*!   _dash_frames_take(f, v)
*!       "" when frame f keeps v under its name, else its split column
*!       __dashm<k>.
*!
*!   _dash_frames_lset(lab)
*!       "" when value label lab travels under its name, else its copy
*!       __dashl<j>.
*!
*!   _dash_frames_cols_json()
*!       The spec's build_options.frame_cols object.
*!
*!   _dash_filter_exclude_add(filter, k, names)
*!       filter with names added to group k's exclude().
*!
*!   _dash_link_split(link)
*!       link()'s groups, split at each "||" (WP-33 33-07 reads them).
*!
*!   _dash_blank_words(s)
*!       The words of s between runs of ASCII blanks, quotes and all.
*!
*!   _dash_extract_filters(filter_out, cmd_out)
*!       Every filter() in the caller's `0': the groups, joined with
*!       " || ", into the local filter_out, and `0' without them into
*!       cmd_out.
*!
*!   _dash_extract_links(link_out, cmd_out)
*!       Two or more link() copies in the caller's `0': their texts,
*!       joined with " || " (one link group each), into link_out, and
*!       `0' without them into cmd_out; one copy or none leaves both "".
*!
*!   _dash_filter_refusal(filter, registry, vars_out)
*!       "" when every filter() group names a variable and only registered
*!       exclude() names, and any direction() is ltr or rtl on a slider or
*!       range, the variables then in vars_out; else the refusal.
*!
*!   _dash_link_refusal(link, registry)
*!       "" when link() is _all alone or each group names only registered
*!       graphs, none in two groups, else the refusal.
*!
*!   _dash_filter_setvars(filter, names)
*!       filter with each group's variable replaced by the next of names.
*!
*!   _dash_json_get_str(json_str, key, out_macro)
*!       The string value of key in json_str, its escapes decoded, into
*!       out_macro; "" when json_str has no such key.
*!
*!   _dash_item_globals(name, out_macro)
*!       The globals one registry item owns that Stata holds, by exact name:
*!       dash_json_<name>, dash_spec_<name>,
*!       dash_kpi_<name> and dash_kpi_<name>__<field> for each field
*!       _dash_kpi_fields() lists, and an image panel's dash_img_<name>
*!       and dash_img_<name>__pth, __cap, __alt and __lnk.
*!
*!   _dash_option_names(in_macro, out_macro)
*!       The option names in the option text held by the local in_macro,
*!       blank-separated, into out_macro.
*!
*!   _dash_has_name_opt(s)
*!       1 when the option text s holds a name() option (spelled name or
*!       nam) at the top level: a second name(), which dash.ado refuses.
*!
*!   _dash_seg_by(seg)
*!       The value of the last non-blank by() option the plot segment seg
*!       gives after its first top-level comma, or "".
*!
*!   _dash_spec_types_in(s, allowed)
*!       1 when the graph spec s names a plot type and every type it names
*!       is a word of allowed: a graph that needs no data.
*!
*!   _dash_spec_has_plots(json)
*!       1 when the spec's "plots" array holds a record, 0 when it is
*!       empty: bare dash's graph, which needs no data.
*!
*!   _dash_reflines_positions(gjson)
*!       The reference-line positions of one graph's JSON: the tokens of
*!       every copy of xline(), yline(), xline2() and yline2() (WP-30
*!       P1.21a), for dash.ado's _dash_reflines_of.
*!
*!   _dash_route_axis2(opts)
*!       opts with each x/y title, label, mlabel, tick, mtick, line and
*!       scale option's axis(2) rewritten as ytitle2()/ylabel2()/
*!       ymlabel2()/ytick2()/ymtick2()/yline2()/yscale2() (x too; the
*!       mlabel and mtick forms WP-31 D1), an axis(1) word dropped and
*!       twoway's plurals renamed; every form twoway refuses is left as typed (WP-28 B3,
*!       WP-29 P0.5).  _dash_axfam(), _dash_ax_parse(), _dash_ax_word()
*!       and _dash_axis_num() (the axis number axis(arg) names, as twoway
*!       reads it: a whole number within -2147483648..2147483647, else 1)
*!       are its internal helpers, shared with _dash_axreq_add.
*!
*!   _dash_axreq_clear()
*!       Empties the external _dash_axreq, the axis options recorded for
*!       the command being parsed (WP-29 P0.5), and the sub-option record
*!       (_dash_subreq_clear, WP-30 P1.19).
*!
*!   _dash_axreq_add(opts, seg)
*!       Records each axis option of the raw option text opts of plot
*!       segment seg (the options after the comma are segment n_segs+1);
*!       column 10 holds twoway's refusal of a label or tick sub-option,
*!       or of a scale word (WP-30 P1.18a).
*!       Records the legend(), zlabel() and title sub-options too
*!       (_dash_subreq_add).
*!
*!   _dash_axbound_list()
*!       Lists, in the caller's locals _axb_n, _axb_k<j>, _axb_o<j> and
*!       _axb_v<j>, the merged axis options twoway bounds when it draws:
*!       each scale's last lwidth() and each label or tick family's last
*!       angle() outside -360..360, axis by axis y1, x1, y2, x2, the scale
*!       first (WP-30 P1.18a).  _dash_angle_out(s) (1 when s is a number
*!       outside -360..360) is its internal helper.
*!
*!   _dash_axreq_check(ys, xs)
*!       Refuses, r(198) with twoway's message and in twoway's order, the
*!       first recorded axis option twoway refuses -- a second comma, an
*!       axis no layer uses (ys, xs: the layers' axes), an axis word in
*!       capitals or given twice, then (column 10) a label, tick or line
*!       sub-option twoway refuses, or r(100) for a line's empty list --
*!       and clears the record; 0 otherwise.  Columns 11-12 hold a line's
*!       positions (WP-30 P1.21a): -1 hands them to dash.ado's
*!       _dash_line_check through its locals _ln_text and _ln_row.
*!
*!   _dash_axreq_accept_line(row)
*!       Marks row's line positions as read by numlist (WP-30 P1.21a).
*!
*!   _dash_axisn_clear()
*!       Empties the external _dash_axisn, the axis options for axes 3-9
*!       that _dash_route_axis2 took out of the option text (WP-31 C10c).
*!
*!   _dash_axisn_json()
*!   _dash_axisn_tf_out()
*!   _dash_axisn_tf_in()
*!       (WP-31 C10e) axes 3-9's x and t rows to and from
*!       _dash_taxis_fold's globals.
*!       The graph's "axisn" object, {"y3":{"label":"...",...},...}: one
*!       entry per letter and axis, one key per family (title label tick
*!       line scale), copies merged as the axis-2 key merges them; "" when
*!       none.  _dash_axisn_add(d, n, family, value), which the route calls,
*!       is its internal helper.
*!
*!   _dash_taxis_unit(fmt, family)
*!       The date unit ("d" "w" "m" "q" "h" "y", "" or "c") twoway reads a
*!       t-option's literal in on an axis of label format fmt: family 1
*!       for labels and ticks, 2 for lines and scale ranges (WP-30 P1.6).
*!
*!   _dash_tdate_ticks(opt, unit)
*!       A tlabel(), ttick(), tmlabel() or tmtick() value (the caller's
*!       _td_in) with its date literals written as numbers, in _td_out;
*!       _td_rc and twoway's words in _td_msg (WP-30 P1.6).  Its helpers
*!       are _dash_tdate_tok(tok, unit, out, bad, single), one position,
*!       (position) or A(d)B rule, and _dash_tdate_value(tok, unit, val):
*!       1 a number or a date of unit (val set), 2 a date of another unit,
*!       3 neither -- the number first, then a whitelist, then Mata's
*!       string date functions (_dash_tdate_lit), never Stata code; a
*!       date in parentheses may hold blanks, (1 jan 2001), and
*!       _dash_tdate_toks(seg) splits a list at the blanks outside
*!       parentheses (WP-44 DG-4).
*!
*!   _dash_tdate_lines(unit)
*!       A tline() value the same way, cut into _td_n pieces _td_s<i>
*!       (_td_k<i> 1 for a copy's positions, 0 for its sub-options).
*!
*!   _dash_tdate_range(unit)
*!       A tscale() value with its range() words made one range() of
*!       numbers; r(121) in _td_rc for a position the unit cannot read.
*!
*!   _dash_taxis_fmt(v)
*!       The argument of the last format() of a label or tick value, the
*!       format its tickset reads the t-options' dates in (WP-30 P1.6).
*!
*!   _dash_xdate_find(v, family)
*!       1 when an x label/tick (1), line (2) or scale (3) value holds a
*!       date literal, which twoway refuses there; _xd_tok names it.
*!
*!   _dash_subreq_check(kind)
*!       Refuses, r(198) with twoway's words, the first legend(), zlabel(),
*!       title or region sub-option twoway refuses (kind legend, zlabel,
*!       title or region; the region's helpers are _dash_subreq_region
*!       and, for the margin() texts twoway fails on with their own rc,
*!       _dash_subreq_margin over _dash_margin_term_rc and
*!       _dash_margin_isnum);
*!       -1 hands a cols()/rows()/holes() value to dash.ado's
*!       _dash_subopt_check through its locals _so_name, _so_value and
*!       _so_kind; prints twoway's legend notes (WP-30 P1.19).  Its helpers
*!       are _dash_subreq_clear, _dash_subreq_add, _dash_subreq_toks,
*!       _dash_subreq_label and _dash_subreq_drop, and twoway's tables and
*!       reader _dash_so_rows, _dash_so_canon, _dash_so_isnum,
*!       _dash_so_family and _dash_so_resolve, the twins of dash_render.py's
*!       _DASH_*_SUBOPT_TABLE and _dash_subopt_resolve.
*!
*!   _dash_subreq_accept()
*!       Marks the value _dash_subreq_check last handed back as passed.
*!
*!   _dash_so_unsafe(s)
*!       1 when s holds a backtick, $, a quote, a backslash or a control
*!       byte: a value never put to -numlist-.
*!
*!   _dash_axis_pieces(s)
*!       An axis-label option's value split into strings, bare runs and
*!       its sub-option tail, into the caller's locals _ap_n, _ap_tag<i>
*!       and _ap_txt<i> (WP-28 S14, GAPS2 B1), and the head's rating
*!       _ap_rule; a rule-led head spends add (WP-30 P1.18b).
*!
*!   _dash_imm_echo(s)
*!       s cut at 80 characters with "..." for a one-line echo (WP-30
*!       P1.5: dash.ado's format() refusal).
*!
*!   _dash_axis_fmts(s)
*!       The format() arguments of an axis-label option's tail, gated, into
*!       the caller's locals _af_n, _af_raw<i>, _af_nw<i>, _af_w<i>_<j> and
*!       _af_ok<i> (WP-30 P1.5).
*!
*!   _dash_zero_obs_rule(t, c)
*!       twoway's answer when plot type t has no observation in case c
*!       (nodata, none, allmissing, byempty): (rc, note line, error line);
*!       rc "0" draws (WP-37 DG-1).
*!
*!   _dash_zero_obs_cvrule(c, discrete)
*!       twoway's answer when a colorvar() layer has no observation in case
*!       c: (rc, error line 1, error line 2); rc "0" draws (WP-42 CV-14).
*!
*!   _dash_zo_records(json, pend)
*!       The records of json's first "plots" array, each its own JSON text;
*!       pend is set to the byte offset of the ] that closes the array.
*!
*!   _dash_cg_reset()
*!       Empties the external table _dash_cg_list of contour grids (WP-37
*!       TR-13), at the start of each export.
*!
*!   _dash_sel_mark(var, gjson)
*!       ORs into byte variable var the rows graph gjson draws: the page
*!       plan's rule, a literal by() graph's panel rows, every row for a
*!       lowess layer with adjust (WP-40 plat:PT-7).
*!
*!   _dash_put_n_obs(gjson, n)
*!       gjson with "n_obs":n, its frame's _N, appended (WP-40 plat:PT-7).
*!
*!   _dash_cg_take(name, k, key, cuts, line, frame, n, lframe)
*!       Appends (name, k, key, object) to _dash_cg_list: object the JSON
*!       {"cuts","line","x","y","z","levels","n"} of twoway__contour_gen's
*!       rows (__cgx __cgy __cgz __cgl) in frame, null for missing, with
*!       "lines" read the same way from lframe when it is not "".
*!
*! Version: 0.1.0  18oct2026

// ============================================================
// Compile into memory
// ============================================================
mata:

// ============================================================
// 1. CHARACTER-LEVEL HELPERS
// ============================================================

// JSON escaping, for a value written between double quotes.
//
// Every byte JSON forbids raw is escaped -- the backslash, the double quote
// and all of C0, as _dash_json_str does in Stata -- and so are the three
// characters a Stata macro could misread once the JSON is expanded: the
// backtick (a macro reference), the dollar (a global) and the apostrophe
// (after a double quote, "' closes a compound quote).  Those are written
// \u00XX, which every JSON reader decodes back to the same character.
//
// This used to append one character at a time, which is quadratic in the
// length, and wrote its escapes with Mata string literals as if Mata read
// \\ as one backslash.  It does not (measured: strlen("\\") is 2), so a
// backslash came out as four and a quote as \\".  Nothing called it then;
// pcarrowi's labels do now (WP-22).  Every character is replaced in one
// subinstr() pass, the backslash first because every escape adds one.
// _dash_dp_format(fmt) -- see the header (WP-31 G2).
string scalar _dash_dp_format(string scalar fmt)
{
    if (c("dp") != "comma") return(fmt)
    if (!ustrregexm(fmt, "^%-?0?[0-9]+[.][0-9]+[fge]c?$")) return(fmt)
    return(subinstr(fmt, ".", ",", 1))
}

string scalar _dash_json_escape(string scalar s) {
    string scalar out, hex, bs
    real   scalar c

    hex = "0123456789abcdef"
    bs  = char(92)
    out = subinstr(s,   bs,       bs + bs,       .)
    out = subinstr(out, char(34), bs + char(34), .)
    out = subinstr(out, char(8),  bs + "b",      .)
    out = subinstr(out, char(9),  bs + "t",      .)
    out = subinstr(out, char(10), bs + "n",      .)
    out = subinstr(out, char(12), bs + "f",      .)
    out = subinstr(out, char(13), bs + "r",      .)
    for (c = 1; c <= 31; c++) {
        if (c == 8 | c == 9 | c == 10 | c == 12 | c == 13) continue
        if (strpos(out, char(c))) {
            out = subinstr(out, char(c), bs + "u00" +
                substr(hex, floor(c / 16) + 1, 1) +
                substr(hex, mod(c, 16) + 1, 1), .)
        }
    }
    out = subinstr(out, char(96), bs + "u0060", .)
    out = subinstr(out, char(36), bs + "u0024", .)
    out = subinstr(out, char(39), bs + "u0027", .)
    return(out)
}

// _html_escape and the wrappers _dash_json_esc and _dash_html_esc were
// removed here (WP-26, 24sep2026): nothing called the wrappers, and
// nothing but _dash_html_esc called _html_escape (GAPS.md N).

// _dash_json_str_args() -- dash.ado's _dash_json_str, read and escaped by
// value.
//
// _dash_json_str is called as  _dash_json_str `"<text>"' <name>  (or with
// the text in plain quotes).  It read its arguments with -args- and escaped
// the text through a chain of subinstr() calls in compound quotes, and both
// parse the text as Stata.  A text holding "' -- a compound-quoted title()
// or legend label does -- ended a compound quote early and came back empty
// or cut, with rc 0 (measured 23sep2026 at ad13a0f: `"A "B" C"' came back
// empty; make == `"AMC"' & foreign == 1 came back as make ==  & foreign ==
// 1).  In plain quotes the text was split at its first inner quote and the
// word after that quote became the NAME the result was stored under -- a
// qualifier chose which of its caller's locals was overwritten.
//
// Here the calling program's `0' is read as a value: its last word is the
// name, and what comes before it is the text, less one pair of enclosing
// quotes, compound or simple.  The text is escaped by _dash_json_escape(), which
// also writes the backtick, the dollar sign and the apostrophe as JSON
// escapes (backslash u 0060, 0024 and 0027), so the result can be
// expanded inside compound quotes -- every spec line is built that way --
// without ending them.  Sets the caller's locals _dash_jsn (the name) and
// _dash_jsv (the escaped text).
void _dash_json_str_args()
{
    string scalar z, t
    real scalar   k, n

    z = strtrim(st_local("0"))
    k = strlen(z)
    while (k > 0) {
        if (substr(z, k, 1) == " " | substr(z, k, 1) == char(9)) break
        k--
    }
    st_local("_dash_jsn", substr(z, k + 1, .))
    t = strrtrim(substr(z, 1, k))
    n = strlen(t)
    if (n >= 4 & substr(t, 1, 2) == char(96) + char(34) &
        substr(t, n - 1, 2) == char(34) + char(39)) {
        t = substr(t, 3, n - 4)
    }
    else if (n >= 2 & substr(t, 1, 1) == char(34) & substr(t, n, 1) == char(34)) {
        t = substr(t, 2, n - 2)
    }
    st_local("_dash_jsv", _dash_json_escape(t))
}

// _dash_scheme_dirs_json() -- the ado-path a scheme dash does not ship is
// looked for along (WP-30 P1.25b, M7).
//
// Stata's setscheme runs findfile scheme-NAME.scheme and then findfile
// NAME.scheme (BASE/s/scheme.class:172-173), and findfile walks c(adopath)
// expanded by pathsubsysdir(), each directory followed by its first-letter
// subdirectory.  The renderer walks the same list, so it is written into
// the spec as build_options.scheme_dirs: at most 64 entries, "." as
// c(pwd), any other relative entry joined to c(pwd), an entry starting ~
// kept as written (the renderer expands it).  An entry holding a backtick,
// a dollar sign, a double quote or a control character is skipped: dash
// never passes such a directory through a macro, a documented difference
// beside the unfollowed link.  Returns the JSON array text; every entry is
// escaped by _dash_json_escape().
string scalar _dash_scheme_dirs_json()
{
    string rowvector d
    string scalar    p, out
    real scalar      i, n, k, bad

    d = pathsubsysdir(pathlist(c("adopath")))
    out = ""
    n = 0
    for (i = 1; i <= cols(d) & n < 64; i++) {
        p = d[i]
        if (p == "") continue
        bad = strpos(p, char(96)) | strpos(p, char(36)) | strpos(p, char(34))
        for (k = 1; k <= strlen(p) & !bad; k++) {
            if (ascii(substr(p, k, 1)) < 32 | ascii(substr(p, k, 1)) == 127) bad = 1
        }
        if (bad) continue
        if (p == ".") p = c("pwd")
        else if (substr(p, 1, 1) != "~" & !pathisabs(p)) p = pathjoin(c("pwd"), p)
        out = out + (n ? "," : "") + char(34) + _dash_json_escape(p) + char(34)
        n++
    }
    return("[" + out + "]")
}

// _dash_text_args(nlead, ntail, optnum) -- a program's arguments read by
// value, around ONE text that may hold anything.
//
// The plot chain handed user text to its helpers as an argument --
//     _dash_process_segment `"<segment>"' _pt_k _json_k 2
//     _dash_validate_value "dash" "by" "byvarlist" `"<value>"' ""
// -- and read it with -args-, which parses the text as Stata.  A text
// holding "' -- title("'90s cars"), the literal of if make == "' or 1 or
// '" -- ended the compound quote around it: the text came back cut, and the
// words after the cut became the arguments that followed it (measured
// 24sep2026: dash scatter mpg weight, title("'90s cars") stopped with
// r(100) ") required", its segment cut at the quote).  This is
// _dash_json_str_args() for any number of arguments.
//
// The calling program's `0' is read as a value.  Its first nlead and last
// ntail arguments are dash's own words -- a name, a plot type, an option
// name, a count, or a plain-quoted word holding no quote of its own, such
// as "dash kpi" or "" -- and the text is what lies between them, less one
// pair of enclosing quotes, compound or plain.  With optnum set, one more
// last argument is taken when it is all digits: an optional count.  Sets
// the caller's locals _dash_txt (the text), _dash_a1, _dash_a2, ... (the
// arguments, the leading ones first, each without its quotes) and _dash_na
// (how many there are).  Only the arguments are scanned, byte by byte; the
// text is cut out by position, in time linear in its length.
void _dash_text_args(real scalar nlead, real scalar ntail, real scalar optnum)
{
    string scalar    z, t
    string rowvector a, b
    real scalar      i, j, k, n, want

    z = st_local("0")
    a = J(1, 0, "")
    b = J(1, 0, "")

    // The leading arguments.
    for (i = 1; i <= nlead; i++) {
        n = strlen(z)
        k = 1
        while (k <= n & (substr(z, k, 1) == " " | substr(z, k, 1) == char(9))) k++
        z = substr(z, k, .)
        if (substr(z, 1, 1) == char(34)) {
            j = strpos(substr(z, 2, .), char(34))
            if (j == 0) j = strlen(z)
            a = a, substr(z, 2, j - 1)
            z = substr(z, j + 2, .)
        }
        else {
            n = strlen(z)
            j = 1
            while (j <= n & substr(z, j, 1) != " " & substr(z, j, 1) != char(9)) j++
            a = a, substr(z, 1, j - 1)
            z = substr(z, j, .)
        }
    }

    // The trailing arguments, the last first.
    want = ntail + (optnum != 0)
    for (i = 1; i <= want; i++) {
        n = strlen(z)
        while (n > 0 & (substr(z, n, 1) == " " | substr(z, n, 1) == char(9))) n--
        z = substr(z, 1, n)
        if (n > 0 & substr(z, n, 1) == char(34)) {
            j = n - 1
            while (j > 0 & substr(z, j, 1) != char(34)) j--
            t = substr(z, j + 1, n - j - 1)
            k = j - 1
        }
        else {
            j = n
            while (j > 0 & substr(z, j, 1) != " " & substr(z, j, 1) != char(9)) j--
            t = substr(z, j + 1, n - j)
            k = j
        }
        // The optional count is taken only when it is one.
        if (i == 1 & optnum) {
            if (!_dash_is_digits(t, .)) continue
        }
        b = t, b
        z = substr(z, 1, max((k, 0)))
    }

    // The text, less one pair of enclosing quotes.
    t = strtrim(z)
    n = strlen(t)
    if (n >= 4 & substr(t, 1, 2) == char(96) + char(34) &
        substr(t, n - 1, 2) == char(34) + char(39)) {
        t = substr(t, 3, n - 4)
    }
    else if (n >= 2 & substr(t, 1, 1) == char(34) & substr(t, n, 1) == char(34)) {
        t = substr(t, 2, n - 2)
    }
    st_local("_dash_txt", t)
    a = a, b
    for (i = 1; i <= cols(a); i++) st_local("_dash_a" + strofreal(i), a[i])
    st_local("_dash_na", strofreal(cols(a)))
}

// UTF-8 byte validation
real scalar _dash_is_utf8(string scalar s) {
    real scalar i, len, b, b2, expect, lo, hi, j

    /*
        Well-formed UTF-8 as RFC 3629 defines it, which is NOT "a lead byte
        in range followed by continuation bytes".  That weaker rule is what
        this used to apply, and measured, it accepted every one of these:

            E0 80 AF        overlong encoding of U+002F
            E0 9F BF        overlong encoding of U+07FF
            F0 80 80 80     overlong encoding of U+0000
            F0 8F BF BF     overlong encoding of U+FFFF
            ED A0 80        UTF-16 surrogate U+D800
            ED BF BF        UTF-16 surrogate U+DFFF
            F4 90 80 80     U+110000, above the Unicode maximum

        Each then reached Python and ended the render with r(7102).  An
        overlong encoding is a classic filter bypass: it spells a character
        the validator upstream did not recognise as that character.

        The second byte is what distinguishes them, so its range depends on
        the lead byte.  The table below is RFC 3629 section 4 verbatim:

            00-7F
            C2-DF  80-BF
            E0     A0-BF  80-BF
            E1-EC  80-BF  80-BF
            ED     80-9F  80-BF      (excludes the surrogates)
            EE-EF  80-BF  80-BF
            F0     90-BF  80-BF 80-BF
            F1-F3  80-BF  80-BF 80-BF
            F4     80-8F  80-BF 80-BF  (stops at U+10FFFF)

        C0 and C1 are excluded already: every two-byte sequence they could
        lead is an overlong encoding of ASCII.
    */

    len = strlen(s)
    i   = 1
    while (i <= len) {
        b = ascii(substr(s, i, 1))

        if (b < 128) {
            i = i + 1
            continue
        }

        if (b >= 194 & b <= 223) {
            expect = 1; lo = 128; hi = 191
        }
        else if (b == 224) {
            expect = 2; lo = 160; hi = 191
        }
        else if (b >= 225 & b <= 236) {
            expect = 2; lo = 128; hi = 191
        }
        else if (b == 237) {
            expect = 2; lo = 128; hi = 159
        }
        else if (b >= 238 & b <= 239) {
            expect = 2; lo = 128; hi = 191
        }
        else if (b == 240) {
            expect = 3; lo = 144; hi = 191
        }
        else if (b >= 241 & b <= 243) {
            expect = 3; lo = 128; hi = 191
        }
        else if (b == 244) {
            expect = 3; lo = 128; hi = 143
        }
        else {
            return(0)
        }

        if (i + expect > len) return(0)

        /* The second byte carries the restricted range. */
        b2 = ascii(substr(s, i + 1, 1))
        if (b2 < lo | b2 > hi) return(0)

        /* Every byte after it is an ordinary continuation. */
        for (j = 2; j <= expect; j++) {
            b = ascii(substr(s, i + j, 1))
            if (b < 128 | b > 191) return(0)
        }

        i = i + expect + 1
    }
    return(1)
}

// ============================================================
// _dash_path_badchar(path)
//
// Returns the byte value of the first character saving() refuses in
// `path', or 0 if there is none.
//
// This lives in Mata because the caller cannot do it in Stata.
// _dash_validate_path's own comment says the backtick and control
// characters are checked with strpos+char() rather than a regex to
// avoid the "too few quotes" crash -- but three checks ran before it,
// each expanding the path inside plain double quotes, so a path
// containing a double quote died in the FIRST of them with r(132) and
// the check written to catch that character never executed.  A Mata
// string read through st_local() is a value, not macro text, so
// nothing the path contains can be parsed as code.
//
// Bytes rejected: the double quote, backquote and dollar sign, which
// Stata would read as macro text (or which end the quoted argument), and
// every control character (1-31, 127), as dash_render.py's
// _validate_output_path refuses them.  ; & | < > and a .. segment are
// accepted, as twoway's saving() accepts them (WP-30 P1.27, M11): the
// opener single-quotes the path on a Mac and Unix, and declines cmd's
// metacharacters on Windows (_dash_cmd_metachar).  Scanning bytes
// rather than characters is deliberate: no byte of a multibyte UTF-8
// character is below 128.  Parentheses are NOT rejected --
// every call site quotes the path, inside which they are literal, and
// rejecting them broke every Windows path under "Program Files (x86)".
// ============================================================
real scalar _dash_path_badchar(string scalar path) {
    real scalar      i, c, n
    real rowvector   bad

    bad = (34, 96, 36, (1..31), 127)
    n   = strlen(path)
    for (i = 1; i <= n; i++) {
        c = ascii(substr(path, i, 1))
        if (anyof(bad, c)) return(c)
    }
    return(0)
}

// ============================================================
// _dash_cmd_metachar(path)
//
// Returns the byte value of the first character in `path' that
// Windows' command shell would read in a double-quoted argument, or 0
// if there is none (WP-30 P1.29, M11).
//
// _dash_open_page opens a page on Windows with `start "" "<path>"',
// which runs inside cmd.exe.  Double quotes do not make a path literal
// there: cmd.exe expands %NAME% inside them, ! under delayed expansion,
// and reads ^ as its escape and & | < > ; as its separators wherever its
// quoting fails.  So start could open another file than the one dash
// wrote.  The opener builds no command for such a path on Windows; the
// page is written and its path printed.  twoway's saving() accepts %, !
// and ^ (measured), so the validator does not refuse them.
//
// Bytes flagged: % ! ^ & | < > ;.  Scanning bytes, as
// _dash_path_badchar does: no byte of a multibyte UTF-8 character is
// below 128, so none of them is flagged.
// ============================================================
real scalar _dash_cmd_metachar(string scalar path) {
    real scalar      i, c, n
    real rowvector   bad

    bad = (37, 33, 94, 38, 124, 60, 62, 59)
    n   = strlen(path)
    for (i = 1; i <= n; i++) {
        c = ascii(substr(path, i, 1))
        if (anyof(bad, c)) return(c)
    }
    return(0)
}

// ============================================================
// twoway's command form (WP-30 P1.27)
//
// _dash_prefix_word, _dash_saving_split, _dash_saving_parse,
// _dash_seg_saving, _dash_launch_quote and _dash_launch_warn.  Every one
// reads its text by value (st_local, never macro text) and is linear in
// the length of what it reads.
// ============================================================

// _dash_prefix_word() -- dash replaces twoway, so a twoway command word
// after dash is what it is after twoway: not a plot type.  `twoway
// twoway ...', `twoway tw ...', `twoway graph ...' and the rest are each
// "<word> is not a twoway plot type", r(198) (measured 14oct2026, StataNow
// 19.5, for twoway tw two twow twowa graph gr gra grap and capitalised
// spellings).  Sets the caller's local _pf_word to the first word of `0'
// when it is one of those nine in any case, else "".  One anchored regex;
// the word is compared from a closed list.
void _dash_prefix_word()
{
    string scalar w

    w = (ustrregexm(st_local("0"), "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
    if (!anyof(("twoway", "tw", "two", "twow", "twowa", "graph", "gr",
                "gra", "grap"), strlower(w))) w = ""
    st_local("_pf_word", w)
}

// _dash_saving_opt_toks(o) -- the words of saving()'s option text, with
// each comma outside quotes and parentheses as a token of its own.
// Linear in the length of o.
string rowvector _dash_saving_opt_toks(string scalar o)
{
    string rowvector out
    string scalar    ch
    real scalar      i, n, depth, in_dq, in_cq, nxt, start, k

    n     = strlen(o)
    out   = J(1, 16, "")
    k     = 0
    depth = 0
    in_dq = 0
    in_cq = 0
    start = 0
    i     = 1
    while (i <= n) {
        nxt = _dash_quote_step(o, n, i, in_dq, in_cq)
        if (nxt) {
            if (!start) start = i
            i = nxt
            continue
        }
        ch = substr(o, i, 1)
        if (depth == 0 & (ch == " " | ch == char(9) | ch == ",")) {
            if (start) {
                if (k == cols(out)) out = out, J(1, cols(out), "")
                out[++k] = substr(o, start, i - start)
                start = 0
            }
            if (ch == ",") {
                if (k == cols(out)) out = out, J(1, cols(out), "")
                out[++k] = ","
            }
            i++
            continue
        }
        if (ch == "(") depth++
        else if (ch == ")" & depth > 0) depth--
        if (!start) start = i
        i++
    }
    if (start) {
        if (k == cols(out)) out = out, J(1, cols(out), "")
        out[++k] = substr(o, start, n - start + 1)
    }
    return(k ? out[|1 \ k|] : J(1, 0, ""))
}

// _dash_saving_split(s) -- saving()'s text, as typed, read as twoway reads
// it (gr_save.ado: syntax anything [, REPLACE ASIS]).  Returns (file,
// replace, asis, comma, err): replace, asis and comma are "0"/"1", err ""
// or twoway's own words (measured, StataNow 19.5; the fixture
// twoway_command_form_truth.json holds them).  The name is the text before
// the first comma outside quotes and parentheses, less one enclosing pair
// of quotes; an empty name is twoway's Graph; a name of two words is
// refused "invalid syntax,  <rest> not allowed".  replace and asis are
// full lower-case words, once each.  Internal to _dash_saving_parse.
// Linear in the length of s.
string rowvector _dash_saving_split(string scalar s)
{
    string rowvector t, o
    string scalar    f, err, w, nm
    real scalar      p, n, i, j, rep, asis, k

    err  = ""
    rep  = 0
    asis = 0
    p    = _dash_first_comma_pos(s)
    f    = strtrim(p ? substr(s, 1, p - 1) : s)

    // The name.
    if (f == "") f = "Graph"
    else {
        t = _dash_rep_toks(f, 0)
        n = cols(t)
        if (n > 1) {
            err = "invalid syntax,  " + invtokens(t[|2 \ n|], " ") + " not allowed"
        }
        else if (n == 1) {
            w = t[1]
            k = strlen(w)
            if (k >= 2 & substr(w, 1, 1) == char(34) & substr(w, k, 1) == char(34)) {
                f = substr(w, 2, k - 2)
            }
            else if (k >= 4 & substr(w, 1, 2) == char(96) + char(34) &
                     substr(w, k - 1, 2) == char(34) + char(39)) {
                f = substr(w, 3, k - 4)
            }
            if (f == "") f = "Graph"
        }
    }

    // The sub-options, left to right; the first problem is the error.
    if (p & err == "") {
        o = _dash_saving_opt_toks(substr(s, p + 1, .))
        n = cols(o)
        // A second comma followed by a word is refused before any option
        // word is judged, as twoway refuses saving(n1, bogus, replace)
        // "invalid 'replace'" (measured; the fixture).
        for (i = 1; i <= n & err == ""; i++) {
            if (o[i] != ",") continue
            for (j = i + 1; j <= n; j++) if (o[j] != ",") break
            if (j <= n) err = "invalid '" + o[j] + "'"
            break
        }
        for (i = 1; i <= n & err == ""; i++) {
            w = o[i]
            if (w == ",") break
            if (w == "replace" | w == "asis") {
                if ((w == "replace" & rep) | (w == "asis" & asis)) {
                    err = "option " + w + " not allowed"
                }
                else if (w == "replace") rep = 1
                else asis = 1
                continue
            }
            nm = _dash_rep_optname(w)
            if (nm != "" & strpos(w, "(")) {
                if (nm == "replace" | nm == "asis") {
                    err = "option " + nm + "() incorrectly specified"
                }
                else err = "option " + nm + "() not allowed"
                continue
            }
            // A quoted word: twoway's message drops its closing quote,
            // option "replace not allowed (measured; the fixture).
            k = strlen(w)
            if (k >= 2 & substr(w, 1, 1) == char(34) & substr(w, k, 1) == char(34)) {
                w = substr(w, 1, k - 1)
            }
            err = "option " + w + " not allowed"
        }
    }
    return((f, strofreal(rep), strofreal(asis), strofreal(p > 0), err))
}

// _dash_saving_parse(s, ext) -- the one saving() grammar of the one-line
// form and dash build (HTML, ext "html", and server, ext "py").  Refuses,
// r(198), what twoway refuses, in twoway's words; else sets the caller's
// locals _sv_file (the name: a .gph suffix replaced, "." + ext appended
// unless it ends so), _sv_replace ("replace"/""), _sv_asis ("asis"/"";
// accepted, no effect), _sv_gph ("1" when .gph was replaced) and
// _sv_comma ("1" when the text has a comma), _sv_img (the graph export
// suffix replaced, or "").  Helper:
// _dash_saving_split().  Linear in the length of s.
void _dash_saving_parse(string scalar s, string scalar ext)
{
    string rowvector r, sfx
    string scalar    f, gph, img, stem
    real scalar      k, n

    r = _dash_saving_split(s)
    if (r[5] != "") {
        _dash_say("err", "", r[5], "")
        exit(198)
    }
    f   = r[1]
    gph = ""
    if (strlen(f) >= 4 & strlower(substr(f, strlen(f) - 3, 4)) == ".gph") {
        f   = substr(f, 1, strlen(f) - 4)
        gph = "1"
    }
    // WP-30 P1.28a: a suffix graph export writes -- its own eleven
    // (gr_export.ado's VerifySuffix, measured) -- is replaced, not kept:
    // twoway's saving(t.png) writes a .gph named t.png, and dash writes
    // HTML and says so (_sv_img, the word from this row, never the
    // user's bytes).  .tiff and other names graph export does not
    // recognise are left alone, and a name that would become empty or a
    // bare folder keeps its suffix.
    img = ""
    if (gph == "") {
        sfx = ("png", "svg", "pdf", "eps", "ps", "jpg", "jpeg", "tif",
               "gif", "emf", "wmf")
        for (k = 1; k <= cols(sfx); k++) {
            n = strlen(sfx[k]) + 1
            if (strlen(f) <= n) continue
            if (strlower(substr(f, strlen(f) - n + 1, n)) != "." + sfx[k]) continue
            stem = substr(f, 1, strlen(f) - n)
            if (substr(stem, -1, 1) == "/" | substr(stem, -1, 1) == char(92)) continue
            f   = stem
            img = sfx[k]
            break
        }
    }
    if (strlen(f) < strlen(ext) + 1 |
        strlower(substr(f, strlen(f) - strlen(ext), .)) != "." + strlower(ext)) {
        f = f + "." + ext
    }
    st_local("_sv_file", f)
    st_local("_sv_replace", r[2] == "1" ? "replace" : "")
    st_local("_sv_asis", r[3] == "1" ? "asis" : "")
    st_local("_sv_gph", gph)
    st_local("_sv_comma", r[4] == "1" ? "1" : "")
    st_local("_sv_img", img)
}

// _dash_seg_saving(seg) -- the value of the last saving() a segment or an
// after-comma list gives, exactly as typed, or "".  syntax's
// SAVing(string) drops every pair of quotes, so saving("n, replace") and
// saving(n, replace) arrive alike (measured); this reads the option words
// as _dash_seg_by does.  sav to saving, lower case (SAVING() is the
// parsers' refusal).  saving() gives "", which twoway treats as absent.
// Linear in the length of seg.
string scalar _dash_seg_saving(string scalar seg)
{
    string rowvector toks
    string scalar    v, out
    real scalar      pos, j

    pos = _dash_first_comma_pos(seg)
    if (pos == 0) return("")
    toks = _dash_rep_toks(substr(seg, pos + 1, .), 0)
    out  = ""
    for (j = 1; j <= cols(toks); j++) {
        if (!anyof(("sav", "savi", "savin", "saving"), _dash_rep_optname(toks[j]))) continue
        if (!strpos(toks[j], "(")) continue
        v = _dash_rep_value(toks[j])
        if (v != "") out = v
    }
    return(out)
}

// _dash_play_find(name, personal) -- the file twoway's play() reads for
// the recording name: gr_play.ado's rule (StataNow 19.5, measured
// 19oct2026).  ".grec" is added when the last part of the path holds no
// "."; the name as given (the working directory, or the path it holds) is
// tried first, then PERSONAL's grec/ folder (personal is c(sysdir_personal)).
// "" when neither exists: twoway looks nowhere else on the ado-path.
string scalar _dash_play_find(string scalar name, string scalar personal)
{
    string rowvector toks
    string scalar    f, last

    toks = tokens(name, "/")
    toks = tokens(toks[cols(toks)], char(92))
    last = toks[cols(toks)]
    f = strpos(last, ".") ? name : name + ".grec"
    if (fileexists(f)) return(f)
    if (fileexists(personal + "grec/" + f)) return(personal + "grec/" + f)
    return("")
}

// _dash_grec_ok(path) -- 1 when the file's first line is a Graph Recorder
// header, "StataFileTM:<version>:01100:GREC:", as _gs_rec_rdfilehdr.ado
// reads it; else twoway says "<file> is not a Graph Recorder file".
real scalar _dash_grec_ok(string scalar path)
{
    real scalar      fh
    string matrix    ln
    string rowvector t

    fh = _fopen(path, "r")
    if (fh < 0) return(0)
    ln = fget(fh)
    fclose(fh)
    if (rows(ln) == 0) return(0)
    t = tokens(ln, ":")
    t = select(t, t :!= ":")
    if (cols(t) < 4) return(0)
    return(strtrim(t[1]) == "StataFileTM" & strtrim(t[3]) == "01100" &
           strtrim(t[4]) == "GREC")
}

// _dash_launch_quote(path, os) -- path quoted for the To launch: line of
// dash build, server.  On a Mac and Unix it is single-quoted, with ' written
// '\'' as _dash_open_page writes it, so nothing in it is special to sh,
// bash or zsh (double quotes left ! to history expansion, measured).  On
// Windows it keeps double quotes (_dash_launch_warn says what cmd.exe
// still expands).  Linear in the length of path.
string scalar _dash_launch_quote(string scalar path, string scalar os)
{
    if (os == "Windows") return(char(34) + path + char(34))
    return(char(39) + subinstr(path, char(39),
           char(39) + char(92) + char(39) + char(39), .) + char(39))
}

// _dash_launch_warn(path, os) -- on Windows, a line saying that cmd.exe
// expands % and ! in a pasted line when the path holds either; else "".
string scalar _dash_launch_warn(string scalar path, string scalar os)
{
    if (os != "Windows") return("")
    if (!strpos(path, "%") & !strpos(path, "!")) return("")
    return("  Windows:   cmd.exe expands % and ! in this path when the line is pasted; run the app from a folder whose path has neither")
}

// _dash_abs_path(path, pwd, os) -- the absolute path of the file a dash
// command wrote, for r(filename) (WP-30 P1.28a): path unchanged when it
// is absolute on os (c(os); "~" counts on a Mac and Unix, as pathisabs()
// says), else pwd, one separator and path.  Nothing is normalised:
// pathjoin() resolves ".." lexically and rewrites a backslash to a slash
// on Unix (measured), and would name a file dash did not write.  Pure,
// no file-system access; linear in the lengths.
string scalar _dash_abs_path(string scalar path, string scalar pwd,
                             string scalar os)
{
    string scalar c1, last, sep

    if (path == "") return("")
    c1 = substr(path, 1, 1)
    if (os == "Windows") {
        if (c1 == "/" | c1 == char(92)) return(path)
        if (strlen(path) >= 2 & substr(path, 2, 1) == ":" &
            ((c1 >= "A" & c1 <= "Z") | (c1 >= "a" & c1 <= "z"))) return(path)
        sep = char(92)
    }
    else {
        if (c1 == "/" | c1 == "~") return(path)
        sep = "/"
    }
    if (pwd == "") return(path)
    last = substr(pwd, -1, 1)
    if (last == "/" | last == char(92)) return(pwd + path)
    return(pwd + sep + path)
}

// _dash_graph_names(list, max) -- the first max names of graph dir,
// memory's list, then "and N more" (WP-30 P1.28a).  The list, not graph
// describe's current graph: after graph drop, graph close or a nodraw
// draw that is not the graph graph export writes (measured).  Linear in
// the length of list.
string scalar _dash_graph_names(string scalar list, real scalar max)
{
    string rowvector t

    t = tokens(list)
    if (cols(t) == 0) return("")
    if (cols(t) <= max) return(invtokens(t))
    return(invtokens(t[1..max]) + " and " + strofreal(cols(t) - max) + " more")
}

void _dash_check_utf8(string scalar s) {
    if (!_dash_is_utf8(s)) {
        errprintf("dash: input contains non-UTF-8 bytes. Ensure your do-file is saved as UTF-8.\n")
        exit(198)
    }
}

// ============================================================
// _dash_smcl_text(s)  and  _dash_say(style, before, value, after)
//
// A message that repeats what the user typed must show it as typed.
// `display' reads its text as SMCL, so an echoed {bf:X} printed a bold X,
// {hline} a rule, and {browse} and {stata} drew links a click would
// follow -- the user's text drawn as Stata's own markup (P19-24..26,
// P20-01..13).  And a value written into a display line through a macro
// is parsed with the line: a double quote in it ended the string, and
// what followed ran as display directives (P9-11..14).
//
// _dash_smcl_text() returns s written in SMCL so that it displays exactly
// as written: { and } become {c -(} and {c )-}.  A control character --
// C0, DEL, or C1 (U+0080..U+009F, the bytes C2 80..C2 9F) -- becomes ?:
// a terminal reads ESC and CSI sequences as commands, and the console
// binary writes to a terminal.  NUL, which no macro can hold, is dropped
// first because it is the placeholder that keeps the two brace
// replacements from rewriting each other.
//
// _dash_say() prints before + value + after as one line in the given SMCL
// style, every piece through _dash_smcl_text() and from Mata, so no piece
// is parsed as Stata code or drawn as markup.  before and after are the
// message's own words; value is read by the caller with st_local().
// ============================================================
string scalar _dash_smcl_text(string scalar s) {
    string scalar t
    real scalar   b

    t = subinstr(s, char(0), "")
    for (b = 1; b <= 31; b++) t = subinstr(t, char(b), "?")
    t = subinstr(t, char(127), "?")
    for (b = 128; b <= 159; b++) t = subinstr(t, char(194) + char(b), "?")
    t = subinstr(t, "{", char(0))
    t = subinstr(t, "}", "{c )-}")
    return(subinstr(t, char(0), "{c -(}"))
}

void _dash_say(string scalar style, string scalar before,
               string scalar value, string scalar after) {
    if (!anyof(("err", "txt", "res"), style)) style = "txt"
    printf("{%s}%s\n", style, _dash_smcl_text(before + value + after))
}

// ============================================================
// _dash_pyname()
//
// The Python dash names in a message (WP-36 plat:PT-1, M8): the one set,
// c(python_exec), or with none set the one Stata found by itself, whose
// path the caller's local _dd_x holds (sys.executable, read by
// _dash_require_deps's version probe).  Shown through _dash_say only.
// ============================================================
string scalar _dash_pyname() {
    string scalar x
    if (c("python_exec") != "") return(c("python_exec"))
    x = st_local("_dd_x")
    if (x != "") return("the Python Stata found, " + x)
    return("the Python Stata found")
}

// ============================================================
// _dash_note(before, value, after)
//
// A note, printed as twoway prints its notes (WP-30 P1.26a).  Measured on
// StataNow 19.5: twoway's named-style note is {txt}(note:  ...) on the
// error stream, which quietly and set output error show and capture
// hides; printf, which _dash_say uses, is hidden by quietly.  So a note is
// one line "(note:  " + text + ")" through errprintf in text colour.  A
// leading "dash: note: " says "note" once; the text is cut to 4,000
// characters and passes _dash_smcl_text, and the format is a constant, so
// the user's text is only ever an argument.  The renderer's twin is
// dash_render.py's _dash_emit_note.
// ============================================================
void _dash_note(string scalar before, string scalar value,
                string scalar after) {
    string scalar t
    t = before + value + after
    if (substr(t, 1, 12) == "dash: note: ") t = "dash: " + substr(t, 13, .)
    if (ustrlen(t) > 4000) t = usubstr(t, 1, 3997) + "..."
    errprintf("{txt}(note:  %s)\n", _dash_smcl_text(t))
}

// ============================================================
// _dash_pcycle_bad(plots, p)
//
// twoway numbers series serid = 1, 2, ... (a ci fit two: its band and its
// line) and draws each in p(mod(serid - 1, p) + 1); a number that is not
// whole -- pcycle(1.5) on three series, mod(2, 1.5) + 1 = 1.5 -- or a p
// of 0 or less is "option seriesid() not allowed", r(198) (WP-31 C8d,
// test/fixtures/pcycle_fraction_truth.json: 1.5 draws on one or two
// series, 2.2 on three, 0.5 on any number).  plots is the graph's plots
// JSON as dash.ado writes it, each plot an object opening {"type":"<t>";
// the series are counted from those openings (an option object that
// opens with a "type" key follows "options": and is skipped).  A ci fit
// with nofit draws its band alone, one series (WP-34 PIC-3,
// ci_plot_index_truth.json pcycle_nofit: (lfitci, nofit) (scatter) is
// drawn under pcycle(1.5)); its plot's text, up to the next plot's
// opening, holds a non-empty "nofit" key.  Returns 1 when twoway refuses.
// ============================================================
real scalar _dash_pcycle_bad(string scalar plots, real scalar p)
{
    real scalar   n, pos, at, k, v, i, q
    real rowvector st
    string rowvector ty
    string scalar t, rest, seg

    if (p >= . | p <= 0) return(1)
    st = J(1, 0, .)
    ty = J(1, 0, "")
    rest = plots
    at = 0
    while ((pos = strpos(rest, `"{"type":""')) > 0) {
        if (!(at + pos > 10 & substr(plots, at + pos - 10, 10) == `""options":"')) {
            t = substr(rest, pos + 9, .)
            t = substr(t, 1, strpos(t, `"""') - 1)
            st = st, at + pos
            ty = ty, t
        }
        at = at + pos
        rest = substr(rest, pos + 1, .)
    }
    n = 0
    for (i = 1; i <= cols(st); i++) {
        if (!anyof(("lfitci", "qfitci", "lpolyci", "fpfitci"), ty[i])) {
            n = n + 1
            continue
        }
        seg = substr(plots, st[i], (i < cols(st) ? st[i + 1] - st[i] : .))
        q = strpos(seg, `""nofit":""')
        n = n + ((q > 0 & substr(seg, q + 9, 1) != `"""') ? 1 : 2)
    }
    for (k = 0; k < n; k++) {
        v = mod(k, p) + 1
        if (v != floor(v)) return(1)
    }
    return(0)
}

// ============================================================
// _dash_colorrule_check(t)
//
// colorrule(crule [%# [*#]]) read as twoway_yxview_parse.class:342-395
// reads it (WP-31 C8b): the text before the first % or * is the rule; a
// %# or *# alone that is not a number is ignored; with both, the
// intensity is confirmed first -- not a number, both ignored (hue %50 *x
// draws hue) -- then the opacity, whose failure is "invalid colorrule
// specification".  A rule twoway has no zyx2rule style for (names are
// case-sensitive: Hue is refused) is refused when the graph is drawn
// (colorvar_options_truth.json R02, R02b, R02c, D04e).  Sets the
// caller's locals _crc ("", "spec" or "rule"), _crn (the rule) and _crf
// (the value with an abbreviated rule written in full, else "").  The
// renderer's twin is dash_render.py's _dash_colorrule_parse.
// ============================================================
// _dash_rightmost_keep(names, flags)
//
// Which copies of the options an option text holds are kept, as twoway
// keeps them (WP-35 MS-1): names[i] is the option token i binds to ("" for
// a token the caller does not read).  1 for a token whose name is "",
// whose name is one of the blank-separated flags (every copy is kept, so
// -syntax- refuses a flag given twice, as twoway refuses it), or whose
// name no later token has; 0 for an earlier copy of a valued option --
// twoway takes the rightmost (twoway_zyx2view_parse.class, _parse combop
// ... rightmost; advanced_options.sthlp).  The names are option names
// dash.ado's _dash_label_split and _dash_contour_split write themselves.
// ============================================================
real rowvector _dash_rightmost_keep(string rowvector names, string scalar flags)
{
    real rowvector k
    real scalar    i, j, n

    n = cols(names)
    k = J(1, n, 1)
    for (i = 1; i <= n; i++) {
        if (names[i] == "" | anyof(tokens(flags), names[i])) continue
        for (j = i + 1; j <= n; j++) {
            if (names[j] == names[i]) {
                k[i] = 0
                break
            }
        }
    }
    return(k)
}

// ============================================================
// _dash_opt_tokens(s)
//
// The top-level options of the option text s, each as typed: s is split at
// blanks that are outside parentheses, plain "quotes" and compound quotes
// (which nest), so levels(5), "a b" and `"x' y"' are one token each (WP-31
// B4b).  Read by value: _dash_contour_split hands each token to -syntax-
// alone and keeps every other one exactly as typed.
// ============================================================
string rowvector _dash_opt_tokens(string scalar s)
{
    string rowvector out
    string scalar    tok, c, c2
    real scalar      i, n, depth, plain, comp

    out = J(1, 0, "")
    tok = ""
    depth = 0
    plain = 0
    comp = 0
    n = strlen(s)
    for (i = 1; i <= n; i++) {
        c = substr(s, i, 1)
        c2 = substr(s, i, 2)
        if (!plain & c2 == char(96) + char(34)) {
            comp++
            tok = tok + c2
            i++
            continue
        }
        if (comp & c2 == char(34) + char(39)) {
            comp--
            tok = tok + c2
            i++
            continue
        }
        if (!comp & c == char(34)) plain = !plain
        else if (!comp & !plain & c == "(") depth++
        else if (!comp & !plain & c == ")" & depth) depth--
        if (c == " " & !depth & !plain & !comp) {
            if (tok != "") out = out, tok
            tok = ""
            continue
        }
        tok = tok + c
    }
    if (tok != "") out = out, tok
    return(out)
}

void _dash_colorrule_check(string scalar t)
{
    string scalar rule, num, other, a, b, inten, opac, full
    real scalar   p1, p2, cut

    st_local("_crc", "")
    st_local("_crn", "")
    st_local("_crf", "")
    t  = strtrim(t)
    if (t == "") return
    p1 = strpos(t, "%")
    p2 = strpos(t, "*")
    cut = (p1 & p2) ? min((p1, p2)) : max((p1, p2))
    rule = t
    if (cut) {
        rule = strtrim(substr(t, 1, cut - 1))
        num  = substr(t, cut + 1, .)
        if (strtoreal(strtrim(num)) >= .) {
            other = (substr(t, cut, 1) == "*" ? "%" : "*")
            if (strpos(num, other)) {
                a = substr(num, 1, strpos(num, other) - 1)
                b = substr(num, strpos(num, other) + 1, .)
                inten = (other == "%" ? a : b)
                opac  = (other == "%" ? b : a)
                if (strtoreal(strtrim(inten)) < . &
                    strtoreal(strtrim(opac)) >= .) {
                    st_local("_crc", "spec")
                    return
                }
            }
        }
    }
    if (rule == "") return
    // The rule's name abbreviates as zyx2rule.class's _unabbrev declares
    // it -- HUE CHUE PHUE LINear INTensity REVLINear, lower case -- so lin
    // is linear and revlinea revlinear to twoway, drawn in the full rule's
    // colours (test_abbreviations.cscript CRA-01); _crf is the value with
    // the full name, the %# or *# part kept, for the caller to write back.
    full = _dash_colorrule_full(rule)
    if (full != "") {
        st_local("_crf", full + substr(t, strlen(rule) + 1, .))
        return
    }
    // twoway's note names the rule's last word: colorrule(hue foo) is
    // "named style foo not found" (R02b).
    st_local("_crc", "rule")
    st_local("_crn", tokens(rule)[cols(tokens(rule))])
}

// _dash_colorrule_full(r) -- the zyx2rule name r spells, or "": hue, chue
// and phue in full, lin .. linear, int .. intensity and revlin ..
// revlinear, as twoway's -syntax- reads them (lower case only: LIN and
// Hue are no spelling, measured 18oct2026).
string scalar _dash_colorrule_full(string scalar r)
{
    string rowvector nm
    real rowvector   mn
    real scalar      i, L

    nm = ("hue", "chue", "phue", "linear", "intensity", "revlinear")
    mn = (3, 4, 4, 3, 3, 6)
    L  = strlen(r)
    for (i = 1; i <= cols(nm); i++) {
        if (L >= mn[i] & L <= strlen(nm[i]) & substr(nm[i], 1, L) == r)
            return(nm[i])
    }
    return("")
}

// ============================================================
// _dash_mlabff_refusal(unk, graph)
//
// mlabfontface() as twoway refuses it (test_abbreviations.cscript MLF-01):
// among the catch-all options unk, a spelling mlabfon .. mlabfontface
// (lower case; mlabf and mlabfo are mlabformat) sets the caller's locals
// _mf_on (1), _mf_rc and _mf_msg to twoway's error.  In a plot's options
// the rightmost copy that is not empty is read: a bare one is "option
// <name> not allowed"; a value is cut at its first blank, "option(s)
// fontface(<word>) not allowed"; a value that opens with a quote, plain
// or compound, is read to its closing quote -- empty, "option(s)
// fontface(`') not allowed"; one word, "option(s) fontface(`<word>"')
// not allowed" invalid name"; with a blank, "option(s) fontface(`<first
// word> not found", r(111) -- all r(198) but the last; a compound-quoted
// one holding an odd number of double quotes is r(132), "option(s)
// fontface(`...too many ')' or ']'", as twoway words it.  After the
// paren-mode comma (graph 1) the first copy is "option <name>() not
// allowed".  None, or only empty copies, which twoway takes: _mf_on 0.
// ============================================================
void _dash_mlabff_refusal(string scalar unk, real scalar graph)
{
    string rowvector toks
    string scalar    tok, nm, v, q, msg, cq, w
    real scalar      i, p, k, rc, cmp, d, nq

    st_local("_mf_on", "0")
    st_local("_mf_rc", "0")
    st_local("_mf_msg", "")
    toks = _dash_opt_tokens(unk)
    msg = ""
    rc = 0
    cq = char(34) + char(39)
    for (i = 1; i <= cols(toks); i++) {
        tok = toks[i]
        p = strpos(tok, "(")
        nm = _dash_mlabff_name(tok)
        if (nm == "") continue
        if (graph) {
            st_local("_mf_on", "1")
            st_local("_mf_rc", "198")
            st_local("_mf_msg", "option " + nm + (p ? "()" : "") + " not allowed")
            return
        }
        if (!p) {
            msg = "option " + nm + " not allowed"
            rc = 198
            continue
        }
        v = substr(tok, p + 1, .)
        if (substr(v, strlen(v), 1) == ")") v = substr(v, 1, strlen(v) - 1)
        v = strtrim(v)
        if (v == "") continue
        q = ""
        cmp = 0
        if (substr(v, 1, 2) == char(96) + char(34)) {
            // To the compound quote that closes it, nested ones kept.
            cmp = 1
            q = substr(v, 3, .)
            d = 1
            for (k = 1; k < strlen(q); k++) {
                if (substr(q, k, 2) == char(96) + char(34)) {
                    d++
                    k++
                }
                else if (substr(q, k, 2) == cq) {
                    if (--d == 0) break
                    k++
                }
            }
            if (d == 0) q = substr(q, 1, k - 1)
        }
        else if (substr(v, 1, 1) == char(34)) {
            q = substr(v, 2, .)
            k = strpos(q, char(34))
            if (k) q = substr(q, 1, k - 1)
        }
        else {
            if (strpos(v, " ")) v = substr(v, 1, strpos(v, " ") - 1)
            msg = "option(s) fontface(" + v + ") not allowed"
            rc = 198
            continue
        }
        q = strtrim(q)
        // A double quote inside a compound-quoted value (measured
        // 18oct2026): with a blank before the first quote the blank rule
        // below; else an odd count is r(132), twoway's line cut where its
        // own display of the value broke, "option(s) fontface(`<text
        // between a leading quote and the next>too many ')' or ']'"; an
        // even count is the one-word refusal, a leading "..." losing its
        // quotes ("ab"c is abc).
        if (cmp & strpos(q, char(34))) {
            k = strpos(q, char(34))
            nq = strlen(q) - strlen(subinstr(q, char(34), ""))
            if (k == 1 | !strpos(substr(q, 1, k - 1), " ")) {
                if (mod(nq, 2)) {
                    w = ""
                    if (k == 1) {
                        w = substr(q, 2, .)
                        if (strpos(w, char(34))) w = substr(w, 1, strpos(w, char(34)) - 1)
                    }
                    msg = "option(s) fontface(" + char(96) + w + "too many ')' or ']'"
                    rc = 132
                    continue
                }
                if (k == 1) {
                    w = substr(q, 2, .)
                    q = substr(w, 1, strpos(w, char(34)) - 1) + substr(w, strpos(w, char(34)) + 1, .)
                }
                msg = (q == "" ? "option(s) fontface(" + char(96) + char(39) + ") not allowed" :
                    "option(s) fontface(" + char(96) + q + cq + ") not allowed" + char(34) + " invalid name")
                rc = 198
                continue
            }
        }
        if (q == "") {
            msg = "option(s) fontface(" + char(96) + char(39) + ") not allowed"
            rc = 198
        }
        else if (strpos(q, " ")) {
            msg = "option(s) fontface(" + char(96) + substr(q, 1, strpos(q, " ") - 1) + " not found"
            rc = 111
        }
        else {
            msg = "option(s) fontface(" + char(96) + q + cq + ") not allowed" + char(34) + " invalid name"
            rc = 198
        }
    }
    if (msg == "") return
    st_local("_mf_on", "1")
    st_local("_mf_rc", strofreal(rc))
    st_local("_mf_msg", msg)
}

// _dash_mlabff_name(tok) -- the spelling of mlabfontface (mlabfon ..
// mlabfontface, lower case) the option token tok is, or "".
string scalar _dash_mlabff_name(string scalar tok)
{
    string scalar nm
    real scalar   p, L

    p = strpos(tok, "(")
    nm = strtrim(p ? substr(tok, 1, p - 1) : tok)
    L = strlen(nm)
    if (L < 7 | L > 12 | substr("mlabfontface", 1, L) != nm) return("")
    return(nm)
}

// _dash_mlabff_strip(s) -- the option text s without the empty
// mlabfontface() copies twoway takes in silence (mlabfontface(),
// mlabfontface( )), so the catch-all note does not name them (MLF-01).
string scalar _dash_mlabff_strip(string scalar s)
{
    string rowvector toks
    string scalar    out, v
    real scalar      i, p

    if (!strpos(s, "mlabfon")) return(s)
    toks = _dash_opt_tokens(s)
    out = ""
    for (i = 1; i <= cols(toks); i++) {
        p = strpos(toks[i], "(")
        if (p & _dash_mlabff_name(toks[i]) != "") {
            v = substr(toks[i], p + 1, .)
            if (substr(v, strlen(v), 1) == ")") v = substr(v, 1, strlen(v) - 1)
            if (strtrim(v) == "") continue
        }
        out = out + (out == "" ? "" : " ") + toks[i]
    }
    return(out)
}

// ============================================================
// _dash_is_digits(s, maxlen)
//
// 1 when s is one or more ASCII digits and nothing else, and at most
// maxlen of them (missing: any number); else 0.  Byte by byte, because no
// regular expression can say this under every caller: under StataNow's
// engine `$' also matches before a trailing newline -- regexm("7" +
// char(10), "^[0-9]+$") is 1, measured -- and under a caller's version
// 16 or 17 the old engine does not know bounded repetition.
// ============================================================
real scalar _dash_is_digits(string scalar s, real scalar maxlen) {
    real scalar i, n, b

    n = strlen(s)
    if (n == 0 | n > maxlen) return(0)
    for (i = 1; i <= n; i++) {
        b = ascii(substr(s, i, 1))
        if (b < 48 | b > 57) return(0)
    }
    return(1)
}

// 1 when the one-byte string ch has a byte value from lo to hi.
real scalar _dash_ascii_in(string scalar ch, real scalar lo, real scalar hi) {
    real scalar b

    if (strlen(ch) != 1) return(0)
    b = ascii(ch)
    return(b >= lo & b <= hi)
}

// ============================================================
// _dash_kpi_pctile(stat, numname, whyname)
//
// Reads a KPI statistic as a percentile, p#, and sets two locals of the
// caller.  <whyname> is
//   "none"    stat is not p followed by digits and points alone, so it is
//             no percentile at all -- mean, pnan, p1e2, P97.5 -- and the
//             caller's list of statistics decides;
//   "form"    p followed by digits and points that make no decimal number:
//             two points (p97.5.5) or no digit (p.);
//   "digits"  more than 15 digits as typed.  A double carries 15 decimal
//             digits faithfully, so every number of 15 digits or fewer is
//             one double to Stata, to Python and to JavaScript -- the three
//             places a card is computed -- and a run of digits too long to
//             be a percentile is refused before anything is done with it;
//   "range"   not greater than 0 and less than 100, the range _pctile
//             accepts: it refuses 0 and 100 with "percentiles must be
//             between 0 and 100", r(198);
//   "ok"      a percentile, and <numname> is its number written once: no
//             leading zero but the one before a point, no trailing zero
//             after it and no point with nothing after it -- p097.50 is
//             97.5, p.5 is 0.5, p5. is 5 -- so the global, the console and
//             both renderers name one percentile one way, and the
//             renderers' p<one or two digits>[.<digits>] reads every one.
// Byte by byte, for _dash_is_digits' reasons: no regular expression says
// this under every caller.
// ============================================================
void _dash_kpi_pctile(string scalar stat, string scalar numname,
                      string scalar whyname)
{
    string scalar body, ip, fp
    real scalar   i, n, b, dots, dotat, v

    st_local(numname, "")
    st_local(whyname, "none")
    if (substr(stat, 1, 1) != "p") return
    body = substr(stat, 2, .)
    n = strlen(body)
    if (n == 0) return
    dots = 0
    dotat = 0
    for (i = 1; i <= n; i++) {
        b = ascii(substr(body, i, 1))
        if (b == 46) {
            dots++
            dotat = i
        }
        else if (b < 48 | b > 57) return
    }
    if (dots > 1 | dots == n) {
        st_local(whyname, "form")
        return
    }
    if (n - dots > 15) {
        st_local(whyname, "digits")
        return
    }
    ip = body
    fp = ""
    if (dots) {
        ip = substr(body, 1, dotat - 1)
        fp = substr(body, dotat + 1, .)
    }
    while (strlen(ip) > 0 & substr(ip, 1, 1) == "0") ip = substr(ip, 2, .)
    while (strlen(fp) > 0 & substr(fp, strlen(fp), 1) == "0") {
        fp = substr(fp, 1, strlen(fp) - 1)
    }
    if (ip == "") ip = "0"
    if (fp != "") ip = ip + "." + fp
    v = strtoreal(ip)
    if (missing(v) | v <= 0 | v >= 100) {
        st_local(whyname, "range")
        return
    }
    st_local(numname, ip)
    st_local(whyname, "ok")
}

// ============================================================
// _dash_layout_cells(layout)
//
// How many cells an explicit layout() grid asks for: rows x cols (each at
// least 1) for layout(rows cols), and for layout(name:row,col ...) the
// rectangle the placements span, read 1-based unless an index is 0.  An
// index longer than nine digits counts as 1e18, larger than any limit.
// Missing when the layout has no size of its own (auto, bs, bs: ...) or is
// not one of the two forms.  dash_render.py's _dash_layout_cells() is the
// same rule, read in ASCII as this one is (test_echo_text.cscript checks
// that the two agree); a layout neither can read, dash build refuses
// (_dash_layout_refusal).
//
// _dash_layout_scan(layout, names) is the reading itself, and also sets
// names to the placement form's names, blank-separated in the order
// written.  Each is an ASCII Stata name; names is meaningful only when the
// count is not missing.
// ============================================================
real scalar _dash_layout_scan(string scalar layout, string scalar names,
                               | string rowvector cells) {
    string scalar s, ch, d1, d2
    real scalar   n, i, j, k, npair, big, allpos, maxr, maxc, r, c, st

    names = ""
    cells = J(1, 0, "")
    s = layout
    for (i = 9; i <= 13; i++) s = subinstr(s, char(i), " ")
    s = strtrim(s)
    n = strlen(s)
    if (n == 0) return(.)

    // rows cols: digits, blanks, digits, and nothing else.
    i = 1
    while (i <= n & _dash_ascii_in(substr(s, i, 1), 48, 57)) i++
    j = i
    while (j <= n & substr(s, j, 1) == " ") j++
    if (i > 1 & j > i & j <= n) {
        k = j
        while (k <= n & _dash_ascii_in(substr(s, k, 1), 48, 57)) k++
        if (k > n) {
            d1 = substr(s, 1, i - 1)
            d2 = substr(s, j, k - j)
            if (strlen(d1) > 9 | strlen(d2) > 9) return(1e18)
            // Each at least 1, as the grid is built.
            return(max((1, strtoreal(d1))) * max((1, strtoreal(d2))))
        }
    }

    // name:row,col placements, blanks allowed around : and , and between.
    npair  = 0
    big    = 0
    allpos = 1
    maxr   = 0
    maxc   = 0
    i = 1
    while (i <= n) {
        while (i <= n & substr(s, i, 1) == " ") i++
        if (i > n) break
        ch = substr(s, i, 1)
        if (!(_dash_ascii_in(ch, 65, 90) | _dash_ascii_in(ch, 97, 122) | ch == "_")) {
            names = ""
            return(.)
        }
        st = i
        i++
        while (i <= n) {
            ch = substr(s, i, 1)
            if (!(_dash_ascii_in(ch, 48, 57) | _dash_ascii_in(ch, 65, 90) |
                  _dash_ascii_in(ch, 97, 122) | ch == "_")) break
            i++
        }
        names = names + (names == "" ? "" : " ") + substr(s, st, i - st)
        while (i <= n & substr(s, i, 1) == " ") i++
        if (i > n) return(.)
        if (substr(s, i, 1) != ":") return(.)
        i++
        while (i <= n & substr(s, i, 1) == " ") i++
        j = i
        while (i <= n & _dash_ascii_in(substr(s, i, 1), 48, 57)) i++
        if (i == j) return(.)
        d1 = substr(s, j, i - j)
        while (i <= n & substr(s, i, 1) == " ") i++
        if (i > n) return(.)
        if (substr(s, i, 1) != ",") return(.)
        i++
        while (i <= n & substr(s, i, 1) == " ") i++
        j = i
        while (i <= n & _dash_ascii_in(substr(s, i, 1), 48, 57)) i++
        if (i == j) return(.)
        d2 = substr(s, j, i - j)
        // Each placement's cell as row,col, without leading zeros, in the
        // order written (WP-31 D14: _dash_layout_refusal compares them).
        cells = cells, (_dash_layout_digits(d1) + "," + _dash_layout_digits(d2))
        npair++
        if (strlen(d1) > 9 | strlen(d2) > 9) big = 1
        else {
            r = strtoreal(d1)
            c = strtoreal(d2)
            if (r == 0 | c == 0) allpos = 0
            if (r > maxr) maxr = r
            if (c > maxc) maxc = c
        }
    }
    if (npair == 0) return(.)
    if (big) return(1e18)
    if (allpos) return(maxr * maxc)
    return((maxr + 1) * (maxc + 1))
}

// _dash_layout_digits(d): ASCII digits d without its leading zeros ("0"
// for zeros only), so 01,1 and 1,1 are one cell however long the digits.
string scalar _dash_layout_digits(string scalar d) {
    real scalar i

    i = 1
    while (i < strlen(d) & substr(d, i, 1) == "0") i++
    return(substr(d, i, .))
}

real scalar _dash_layout_cells(string scalar layout) {
    string scalar names

    return(_dash_layout_scan(layout, names))
}

// 1 when s is an ASCII Stata name: a letter or _, then letters, digits, _.
real scalar _dash_is_name(string scalar s) {
    real scalar i, n

    n = strlen(s)
    if (n == 0) return(0)
    if (!(_dash_ascii_in(substr(s, 1, 1), 65, 90) | _dash_ascii_in(substr(s, 1, 1), 97, 122) |
          substr(s, 1, 1) == "_")) return(0)
    for (i = 2; i <= n; i++) {
        if (!(_dash_ascii_in(substr(s, i, 1), 48, 57) | _dash_ascii_in(substr(s, i, 1), 65, 90) |
              _dash_ascii_in(substr(s, i, 1), 97, 122) | substr(s, i, 1) == "_")) return(0)
    }
    return(1)
}

// 1 when s is a Stata name (G5, WP-28): letters -- Unicode ones too, as
// Stata 14+ allows -- digits and _, not starting with a digit, at most 32
// characters (the by() rule of 2916, [U] 11.3).  _dash_is_name above stays
// ASCII-only on purpose: it also validates layout names and option words,
// which are not variable names.
real scalar _dash_is_varname(string scalar s) {
    return(ustrregexm(s, "^[\p{L}_][\p{L}\p{N}_]*$") & ustrlen(s) <= 32)
}

// ============================================================
// _dash_layout_refusal(layout, registry)
//
// "" when dash build can draw layout() as written; otherwise the refusal,
// without the command's name.  The value's START used to be all that was
// checked (bs..., or name:r,c...), so the renderer was handed what it could
// not read and drew it some other way, in silence (P20-30): measured at
// f2ecdd4, layout(p:1,1 junk) and layout(bs\) were drawn as auto,
// layout(nosuch:1,1) was a 3 x 1 grid saved and 1 x 2 served, and
// layout(bs: ...) dropped an unknown name and clamped a span of 13 to 12.
//
// The value must be one of the forms whole -- rows cols or name:row,col
// placements as _dash_layout_scan() reads them; bs; or bs: followed by
// rows of name or name=span separated by / -- every name must be in
// registry, as link() and exclude() require, and placed once, and every
// span a whole number from 1 to 12 written in at most two digits.  dash_render.py's
// _dash_layout_check() reports the same problems in a spec that did not
// come through dash.ado.
// ============================================================
string scalar _dash_layout_refusal(string scalar layout, string scalar registry) {
    string scalar    s, form, names, spec, tok, nm, span
    string rowvector reg, nms, toks, seen, cells
    real scalar      i, j, eq

    form = "layout() must be 'auto', 'N M' grid (N and M >= 1), " +
           "'name:row,col' placement, or 'bs[: name=span ...]' Bootstrap layout."
    s = layout
    for (i = 9; i <= 13; i++) s = subinstr(s, char(i), " ")
    s = strtrim(s)
    if (s == "" | s == "auto") return("")
    reg = tokens(registry)

    // A value that reads whole as placements or a grid is one, whatever
    // its first letters: layout(bsales:1,1 g2:1,2) places a graph named
    // bsales, and was refused as a malformed bs layout (measured
    // 23sep2026).  dash_render.py's _dash_is_bs_layout() is the same rule.
    if (strlower(substr(s, 1, 2)) == "bs" & missing(_dash_layout_scan(s, names))) {
        spec = strtrim(substr(s, 3, .))
        if (spec == "") return("")
        if (substr(spec, 1, 1) != ":") return(form)
        spec = strtrim(substr(spec, 2, .))
        if (spec == "") return(form)
        spec = subinstr(spec, "/", " ")
        toks = tokens(spec)
        seen = J(1, 0, "")
        for (i = 1; i <= cols(toks); i++) {
            tok = toks[i]
            eq  = strpos(tok, "=")
            nm  = (eq ? substr(tok, 1, eq - 1) : tok)
            if (!_dash_is_name(nm)) return(form)
            if (!anyof(reg, nm)) return("layout() name '" + nm + "' not found in registry.")
            // A name placed twice: the saved page embedded it once per
            // repeat -- 100,000 made an 18.1 MB page (WP-21).
            if (anyof(seen, nm)) return("layout() places '" + nm + "' more than once.")
            seen = seen, nm
            if (eq) {
                span = substr(tok, eq + 1, .)
                if (!_dash_is_digits(span, 2)) {
                    return("layout() span in '" + tok + "' must be a whole number from 1 to 12.")
                }
                if (strtoreal(span) < 1 | strtoreal(span) > 12) {
                    return("layout() span in '" + tok + "' must be a whole number from 1 to 12.")
                }
            }
        }
        return("")
    }

    names = ""
    if (missing(_dash_layout_scan(s, names, cells))) return(form)
    nms = tokens(names)
    for (i = 1; i <= cols(nms); i++) {
        if (!anyof(reg, nms[i])) return("layout() name '" + nms[i] + "' not found in registry.")
        // Placed twice, it kept its last place without a word.
        if (i > 1) {
            if (anyof(nms[|1 \ i - 1|], nms[i])) {
                return("layout() places '" + nms[i] + "' more than once.")
            }
        }
        // Two names in one cell: the second took the cell in the served
        // app and the first vanished, without a word (WP-31 D14).
        if (i > 1) {
            for (j = 1; j < i; j++) {
                if (cells[j] == cells[i]) {
                    return("layout() places '" + nms[j] + "' and '" + nms[i] + "' in the same cell " + cells[i] + ".")
                }
            }
        }
    }
    return("")
}

// _dash_tabs_unwrap(tabs): tabs() less one pair of quotes around the whole
// value, "..." or `"..."', when the value inside holds no double quote;
// else as given (WP-31 D14).  tabs("Main: s1") was read with its quotes,
// so the last name ended in one and was dropped from the tab.
string scalar _dash_tabs_unwrap(string scalar tabs)
{
    string scalar t, q

    q = char(34)
    t = strtrim(tabs)
    if (strlen(t) >= 4 & substr(t, 1, 2) == char(96) + q & substr(t, -2, 2) == q + char(39)) {
        t = substr(t, 3, strlen(t) - 4)
    }
    else if (strlen(t) >= 2 & substr(t, 1, 1) == q & substr(t, -1, 1) == q) {
        t = substr(t, 2, strlen(t) - 2)
    }
    else return(tabs)
    if (strpos(t, q)) return(tabs)
    return(t)
}

// _dash_tabs_refusal(tabs, registry): "" when every name of every tab is
// registered and every per-tab layout() reads whole over that tab's names
// (WP-31 D14); otherwise the refusal, without the command.  Tabs are split
// at /, a tab's title ends at its first colon and its names at the first
// comma after that; what follows the comma is the tab's options, of which
// layout() in the grid or placement form is the only one.  The names were
// dropped from the tab without a word.
string scalar _dash_tabs_refusal(string scalar tabs, string scalar registry)
{
    string rowvector segs, reg, nms, toks
    string scalar    seg, body, opts, lay, nm, r
    real scalar      i, j, c

    reg  = tokens(registry)
    segs = tokens(subinstr(tabs, "/", char(1)), char(1))
    for (i = 1; i <= cols(segs); i++) {
        seg = strtrim(segs[i])
        if (seg == "" | seg == char(1)) continue
        c = strpos(seg, ":")
        body = (c ? substr(seg, c + 1, .) : seg)
        opts = ""
        c = strpos(body, ",")
        if (c) {
            opts = substr(body, c + 1, .)
            body = substr(body, 1, c - 1)
        }
        nms = tokens(body)
        for (j = 1; j <= cols(nms); j++) {
            if (!anyof(reg, nms[j])) return("tabs() name '" + nms[j] + "' not found in registry.")
        }
        if (strtrim(opts) == "") continue
        toks = _dash_rep_toks(opts, 1)
        for (j = 1; j <= cols(toks); j++) {
            if (toks[j] == "") continue
            nm = _dash_rep_optname(toks[j])
            if (nm != "layout" | !strpos(toks[j], "(")) {
                return("tabs(): option " + nm + "() not allowed")
            }
            lay = strtrim(_dash_rep_value(toks[j]))
            if (strlower(substr(lay, 1, 2)) == "bs" | lay == "" | lay == "auto") {
                return("tabs(): layout() must be 'N M' grid or 'name:row,col' placement inside a tab.")
            }
            r = _dash_layout_refusal(lay, body)
            if (r != "") return("tabs(): " + r)
        }
    }
    return("")
}

// _dash_axlabel_refusal(text) -- the part of an xlabel()/ylabel()/xtick()/
// ytick() value twoway refuses with r(198) "invalid label specifier, :
// <part>:", or "" when twoway draws it (WP-31 D6; measured,
// test/fixtures/axis_look_truth.json ref_*).  After an optional leading
// rule (#N, ##N, minmax, none, a lone ".", or an a(b)c with a < c:
// _dash_axlabel_lead) twoway reads the rest of the head as values each
// followed by at most one label: a quoted label with no value before it
// ("a"; 1 "a" "b"; 10(10)40 "a"), a second rule (#3 #4) or an unfinished
// a(b)c (1(1)) is refused, and the part named is the head after the
// leading rule.  The values themselves are numlists to twoway
// (_dash_axlabel_runs; WP-44 DG-9).  Linear in the length of text.
string scalar _dash_axlabel_refusal(string scalar text)
{
    string rowvector w
    string scalar    head, rest, t, c
    real scalar      i, p1, p2, prev, bad

    head = _dash_axlabel_head(text)
    if (!cols(_dash_rep_toks(subinstr(head, ",", " "), 0))) return("")
    rest = strtrim(substr(head, _dash_axlabel_lead(head) + 1, .))
    w = _dash_rep_toks(subinstr(rest, ",", " "), 0)
    prev = 0
    bad = 0
    for (i = 1; i <= cols(w); i++) {
        t = w[i]
        c = substr(t, 1, 1)
        if (c == char(34) | c == char(96)) {
            // A label needs a value before it.
            if (prev != 1) bad = 1
            prev = 2
        }
        else if (c == "#") bad = 1
        else {
            p1 = strpos(t, "(")
            p2 = strpos(t, "[")
            // Only a number-led word is a rule: td(1jan2000) is a word
            // numlist refuses (_dash_axlabel_runs).
            if ((p1 | p2) & (strtoreal(substr(t, 1, 1)) < . |
                c == "-" | c == "+" | c == ".") & !_dash_axlabel_rule(t)) bad = 1
            prev = 1
        }
        if (bad) return(rest)
    }
    return("")
}

// _dash_axlabel_custom_refusal(text) -- twoway's line for an axis label or
// tick value whose sub-options hold custom and a label or tick edit
// (style(), angle(), labcolor(), tlcolor(), nolabels ... : the ticksetstyle
// and tickstyle edits of _gs_parse_and_log_tickset.ado) but whose list
// holds no value after its leading rule -- an empty list, a lone a(b)c,
// #N, minmax or none -- which twoway refuses r(198) "tick_styles[-1]
// invalid name" (set_custom has no listed tick to style), or "" (WP-44
// AX-5; measured, test/fixtures/tick_style_truth.json ax5_*: custom alone,
// with grid edits only or with format() is drawn).
string scalar _dash_axlabel_custom_refusal(string scalar text)
{
    string rowvector w, edits
    string scalar    body, sub, head, nm
    real scalar      i, p, cust, ed

    if (!_dash_rep_split(text, body, sub)) return("")
    edits = ("angle", "alternate", "altgap", "style", "novaluelabels",
             "valuelabels", "tlength", "tposition", "labgap", "noticks",
             "ticks", "noshowlabels", "nolabels", "showlabels", "labels",
             "tstyle", "labstyle", "labsize", "labcolor", "labjustification",
             "labalignment", "tlstyle", "tlwidth", "tlcolor", "tlpattern")
    w = _dash_rep_toks(sub, 0)
    cust = 0
    ed = 0
    for (i = 1; i <= cols(w); i++) {
        p = strpos(w[i], "(")
        nm = _dash_so_canon(p ? substr(w[i], 1, p - 1) : w[i], "axlabel")
        if (nm == "custom") cust = 1
        else if (anyof(edits, nm)) ed = 1
    }
    if (!cust | !ed) return("")
    head = strtrim(body)
    if (strtrim(substr(head, _dash_axlabel_lead(head) + 1, .)) != "") return("")
    return("tick_styles[-1] invalid name")
}

// _dash_axlabel_head(text) -- an axis label value's list, trimmed: the
// text before the comma that starts its sub-options (a comma followed by
// a letter, an underscore or nothing, outside quotes).
string scalar _dash_axlabel_head(string scalar text)
{
    string scalar head, c
    real scalar   n, i, k, in_dq, in_cq, nxt

    n = strlen(text)
    head = text
    in_dq = 0
    in_cq = 0
    i = 1
    while (i <= n) {
        nxt = _dash_quote_step(text, n, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }
        if (substr(text, i, 1) == ",") {
            k = i + 1
            while (k <= n & (substr(text, k, 1) == " " | substr(text, k, 1) == char(9))) k++
            c = (k <= n ? substr(text, k, 1) : "")
            if (c == "" | _dash_ascii_in(c, 65, 90) | _dash_ascii_in(c, 97, 122) | c == "_") {
                head = substr(text, 1, i - 1)
                break
            }
        }
        i++
    }
    return(strtrim(head))
}

// _dash_axlabel_lead(head) -- the length of head's leading rule, which
// twoway's Rules (_gs_parse_and_log_tickset.ado) reads before the list:
// a first word #N or ##N, minmax, none or ".", or an a(b)c -- spaced or
// not, (b) a parenthesised number -- with a < c; 0 when there is none.
// a[b]c and a descending a(b)c are list values, not rules (measured,
// test/fixtures/axis_misc_truth.json dg9.desc_rule_word).
real scalar _dash_axlabel_lead(string scalar head)
{
    string rowvector w
    string scalar    t, a, b, c
    real scalar      n, i, j, k, q

    w = _dash_rep_toks(subinstr(head, ",", " "), 0)
    if (!cols(w)) return(0)
    t = w[1]
    if (substr(t, 1, 1) == "#" | t == "minmax" | t == "none" | t == "." |
        (cols(w) == 1 & _dash_axlabel_rule(t))) {
        return(strpos(head, t) + strlen(t) - 1)
    }
    // a, then "(" b ")", then c, blanks allowed between them.
    n = strlen(head)
    i = 1
    while (i <= n & substr(head, i, 1) == " ") i++
    j = i
    while (j <= n & substr(head, j, 1) != " " & substr(head, j, 1) != "(") j++
    a = substr(head, i, j - i)
    while (j <= n & substr(head, j, 1) == " ") j++
    if (a == "" | substr(head, j, 1) != "(") return(0)
    k = strpos(substr(head, j + 1, .), ")")
    if (!k) return(0)
    b = substr(head, j + 1, k - 1)
    q = j + k + 1
    while (q <= n & substr(head, q, 1) == " ") q++
    j = q
    while (j <= n & !anyof((" ", "(", ")"), substr(head, j, 1))) j++
    c = substr(head, q, j - q)
    if (c == "") return(0)
    if (!(strtoreal(a) < . & strtoreal(strtrim(b)) < . & strtoreal(c) < .))
        return(0)
    if (!(strtoreal(a) < strtoreal(c))) return(0)
    return(j - 1)
}

// _dash_axlabel_runs(text) -- the value runs twoway puts to numlist (WP-44
// DG-9): _gs_parse_and_log_tickset.ado's NumTextList reads the list after
// its leading rule as runs of values between labels, each a numlist, so
// a bare word, .a, a missing value, td() or abc(1) is refused, "invalid
// label specifier, :  <the list after its rule>:", r(198) (measured,
// test/fixtures/axis_misc_truth.json dg9.*).  Sets the caller's locals
// _alv_n (the number of runs), _alv<i> (each run, its words joined by one
// blank), _alv_ok<i> (0 when a run holds a byte that may not reach a
// command line: a quote, backtick, dollar sign, backslash or control
// byte -- numlist refuses such a run in twoway, so dash.ado refuses it
// without running it) and _alv_rest (the part named).  Linear in the
// length of text.
void _dash_axlabel_runs(string scalar text)
{
    string rowvector w
    string scalar    head, rest, run, t, c
    real scalar      i, k

    head = _dash_axlabel_head(text)
    rest = strtrim(substr(head, _dash_axlabel_lead(head) + 1, .))
    st_local("_alv_rest", rest)
    w = _dash_rep_toks(subinstr(rest, ",", " "), 0)
    k = 0
    run = ""
    for (i = 1; i <= cols(w) + 1; i++) {
        t = (i <= cols(w) ? w[i] : char(34))
        c = substr(t, 1, 1)
        if (c == char(34) | c == char(96)) {
            if (run != "") {
                k++
                st_local("_alv" + strofreal(k), run)
                st_local("_alv_ok" + strofreal(k), strofreal(!_dash_so_unsafe(run)))
            }
            run = ""
        }
        else run = (run == "" ? t : run + " " + t)
    }
    st_local("_alv_n", strofreal(k))
}

// _dash_axlabel_rule(t) -- 1 when the word t is a whole a(b)c or a[b]c.
real scalar _dash_axlabel_rule(string scalar t)
{
    real scalar p1, p2
    p1 = strpos(t, "(")
    p2 = strpos(t, ")")
    if (!p1) {
        p1 = strpos(t, "[")
        p2 = strpos(t, "]")
    }
    if (!(p1 > 1 & p2 > p1 + 1 & p2 < strlen(t))) return(0)
    return(strtoreal(substr(t, 1, p1 - 1)) < . &
           strtoreal(substr(t, p1 + 1, p2 - p1 - 1)) < . &
           strtoreal(substr(t, p2 + 1, .)) < .)
}



// ============================================================
// 2. PLOT-TYPE ABBREVIATION EXPANSION
// ============================================================

string scalar _dash_expand_plottype_str(string scalar name) {
    string matrix tbl
    string scalar full, minab
    real scalar   i

    // (full name, minimum abbreviation).  Minimums are twoway's own, read
    // from the declaration its plot types are parsed by (twowaygraph_g.class
    // _unab_cmd: SCatter LIne CONnected HISTogram RSCatter RLine RCONnected
    // MBANDs FN FUNction) and recorded in test/fixtures/abbrev_truth.json;
    // every other type is its full name.  Nothing shorter is taken: dash
    // took thirteen shorter spellings twoway refuses, "ar is not a twoway
    // plot type", r(198) (WP-31 A2, DISCOVERY Q28;
    // test/fixtures/bare_prefix_truth.json extras.*).
    //
    // Matching below accepts ANY prefix at least as long as the minimum, the
    // way Stata does, replacing the fixed one-short-form-each table that
    // rejected every other prefix.
    tbl = ("scatter","sc") \
        ("line","li") \
        ("connected","con") \
        ("area","area") \
        ("bar","bar") \
        ("spike","spike") \
        ("lfit","lfit") \
        ("qfit","qfit") \
        ("lfitci","lfitci") \
        ("qfitci","qfitci") \
        ("lowess","lowess") \
        ("lpoly","lpoly") \
        ("lpolyci","lpolyci") \
        ("fpfit","fpfit") \
        ("fpfitci","fpfitci") \
        ("histogram","hist") \
        ("kdensity","kdensity") \
        ("rarea","rarea") \
        ("rbar","rbar") \
        ("rspike","rspike") \
        ("rcap","rcap") \
        ("rline","rl") \
        ("rconnected","rcon") \
        ("dot","dot") \
        ("dropline","dropline") \
        ("rcapsym","rcapsym") \
        ("pcspike","pcspike") \
        ("pcarrow","pcarrow") \
        ("pcbarrow","pcbarrow") \
        ("pci","pci") \
        ("pcscatter","pcscatter") \
        ("tsline","tsline") \
        ("tsrline","tsrline") \
        ("mspline","mspline") \
        ("mband","mband") \
        ("rscatter","rsc") \
        ("function","fun") \
        ("scatteri","scatteri") \
        ("pccapsym","pccapsym") \
        ("pcarrowi","pcarrowi") \
        ("rpcap","rpcap") \
        ("rpspike","rpspike") \
        ("contour","contour") \
        ("contourline","contourline")
    // pccapsym and pcarrowi (WP-22): twoway takes neither by any shorter
    // name -- measured 23sep2026, pc .. pccapsy and pcarr, pcarro are "not
    // a twoway plot type", and pcarrow is its own type -- so the minimum
    // is the full name.  pcarrow still wins "pcarrow": pcarrowi's
    // minimum is eight letters.  rpcap and rpspike (WP-31 B1): full names
    // only -- rpca and rpspik are "not a twoway plot type" (measured
    // 23sep2026 and 14oct2026, test/fixtures/rangept_truth.json abbrev.*).
    // contour and contourline (WP-31 B4b): full names only -- cont ..
    // contou and contourl .. contourlin are "not a twoway plot type"
    // (measured 23sep2026); neither row claims the other's name, since a
    // name matches only from its row's minimum.

    // twoway's two spellings that are no prefix of the name, from the
    // declaration its plot types are read by (twowaygraph_g.class, program
    // _unab_cmd): `syntax [, SCatter LIne CONnected HISTogram RSCatter
    // RLine RCONnected MBANDs FN FUNction *]'.  MBANDs takes mband and
    // mbands; FN is function.  Measured 23sep2026: `twoway mbands mpg
    // weight' and `twoway fn y=x' are rc 0, and dash refused both, r(198),
    // where dash.sthlp says a plot type is "abbreviated as twoway allows"
    // (test_help_claims_1.cscript HC1-07).
    if (name == "mbands") return("mband")
    if (name == "fn") return("function")

    // A name is the one row whose full name it begins and whose minimum it
    // reaches: no name reaches two rows, so the first it reaches is the
    // only one.  This counted the rows a name reached and refused one that
    // reached two, "an ambiguous prefix", which nothing could reach (WP-26
    // TR-26.6, measured 24sep2026 at 480159f): each of the 186 prefixes of
    // the 40 names reached at most one row.  Nor has twoway an ambiguous
    // plot type to refuse.  Of the 209 prefixes of the 45 plot-type names
    // probed (these 40 and the four dash refuses by name) it took each as
    // the one type whose minimum it reaches, or refused it, "s is not a
    // twoway plot type", r(198) -- s, r, pc, rc and every other prefix of
    // two names that reaches neither minimum among them -- which is what
    // dash says too, in those words (WP-31 A2).  test_parser.cscript P1A-76 and
    // test_no_orphans.py fail when a row lets a name reach two.
    for (i = 1; i <= rows(tbl); i++) {
        full  = tbl[i,1]
        minab = tbl[i,2]
        if (strlen(name) >= strlen(minab) &
            substr(full, 1, strlen(name)) == name) return(full)
    }
    return("")   // no plot type dash draws
}

// The word as typed: a capital letter makes it no plot type, as twoway
// reads it (WP-35 plot:PT-3).
void _dash_expand_plottype(string scalar abbrev, string scalar out_macro) {
    st_local(out_macro, _dash_expand_plottype_str(strtrim(abbrev)))
}


// ============================================================
// 2b'. KERNEL NAMES   (kernel() of lpoly, lpolyci and kdensity)
// ============================================================
//
// twoway takes each kernel name down to its minimum abbreviation --
// EPanechnikov, BIweight, COSine, GAUssian, PARzen, RECtangle, TRIangle,
// and epan2 only in full -- on lpoly, lpolyci and kdensity alike (measured
// 24sep2026, every prefix of every name: ep, epa and epan are
// epanechnikov; e, co, ga, pa, re and tr are refused, r(198)).  dash's
// rule table (kernel=enum) takes the full names only, so kernel(gau) was
// refused where twoway draws it.  Returns the full name, lower case, for
// a word twoway takes, and the word as given otherwise, for the enum rule
// to refuse with its message.  Read by value; the word is the user's text.
string scalar _dash_kernel_full(string scalar word) {
    string scalar s
    string rowvector full
    real rowvector minlen
    real scalar i

    s = strlower(strtrim(word))
    if (s == "epan2") return(s)
    full   = ("epanechnikov", "biweight", "cosine", "gaussian", "parzen",
              "rectangle", "triangle")
    minlen = (2, 2, 3, 3, 3, 3, 3)
    for (i = 1; i <= cols(full); i++) {
        if (strlen(s) >= minlen[i] & strlen(s) <= strlen(full[i]) &
            substr(full[i], 1, strlen(s)) == s) return(full[i])
    }
    return(word)
}


// ============================================================
// 2c. IMMEDIATE VALUES   (scatteri, pci, pcarrowi)
// ============================================================
//
// The immediate values of twoway scatteri, pci and pcarrowi, one record
// each (twoway_scatteri.sthlp, twoway_pci.sthlp, twoway_pcarrowi.sthlp):
//
//     scatteri   #y #x               [(#clockposstyle)] ["text for label"]
//     pci        #y1 #x1 #y2 #x2     [(#clockposstyle)] ["text for label"]
//     pcarrowi   #y1 #x1 #y2 #x2     [(#clockposstyle)] ["text for label"]
//
// read here as twoway's own parsers read them: twoway_scatteri_parse.class
// and twoway_pci_parse.class, which pcarrowi's inherits unchanged.  Each
// takes a record's coordinates with gettoken, then gettoken with
// match(p) quotes for an optional clock position, then gettoken with
// quotes for an optional label, and loops while the record's LAST
// coordinate is not empty.  What that does was measured 23sep2026 with
// the console binary, loading the serset each command draws and reading
// each graph's SVG export:
//
//   * a coordinate is a number as numlist reads one; blanks around it are
//     allowed, a tab or any other character is not.  "." and .a-.z are
//     missing and draw nothing; so does a number past a double's range
//     (1e400, 1e308) and one past a float's (1e39): twoway stores the
//     values as float;
//   * a coordinate in quotes is a number where gettoken strips the quotes
//     -- the first of the list, every one but a record's first, and the
//     first after a label.  Straight after a record, or after its clock
//     position, a quoted token is that record's label;
//   * a clock position comes before the label, never after it: one written
//     after the label is read as the next record's first coordinate.  A
//     second label is read the same way;
//   * a token that is not a number where a coordinate belongs is refused,
//     "invalid point," r(198);
//   * a clock position that is not a number from 0 to 12 is refused,
//     "invalid position, 13" r(198).  3.5, 012 and 1e1 are taken;
//   * the loop ends where a record's last coordinate is empty: at the end
//     of the list -- what is left, too little for another record, is
//     dropped without a word (scatteri 1 2 3 draws one point, rc 0) -- or
//     at a quoted "" in that place, which drops the rest of the list too;
//   * a list with no whole record is refused, "'0' invalid observation
//     number," r(198).
//
// A numlist range that holds one number twoway then evaluates as a
// division, and so does dash (WP-31 C18, measured,
// test/fixtures/parsed_values_truth.json): p/q with p == q draws 1 --
// 2/2 and -1/-1 draw at 1, 0/0 is missing, (1/1) is the clock position 1
// -- and p != q, a range of two numbers, is "invalid point" in twoway too.
// One thing twoway takes is refused here, because it is an accident of its
// implementation rather than its syntax: a hexadecimal literal at the top
// of a double's range (1.0X+3ff), missing there.
//
// The list is read byte by byte, as a value: nothing in it is ever
// expanded as Stata.  Only a blank separates two tokens, as in gettoken; a
// quoted part binds its blanks, inside a word too; double quotes do not
// nest and compound quotes do; a (group) is read only where a clock
// position may stand.  Every delimiter is ASCII, so a UTF-8 label is never
// split.  Each step is linear in the length of the list: the bytes are
// read once, records are stored in a vector that doubles when full, and
// the JSON is joined once at the end.
// ============================================================

// The position of the double quote that closes the one at i, in the bytes
// b of a list, or cols(b) + 1 when none does.
real scalar _dash_imm_dq_end(real rowvector b, real scalar i)
{
    real scalar j, n

    n = cols(b)
    for (j = i + 1; j <= n; j++) {
        if (b[j] == 34) return(j)
    }
    return(n + 1)
}

// 1 when a compound quote opens at i: a backtick, then a double quote.
// Mata evaluates both sides of & and &&, so the bound is tested apart.
real scalar _dash_imm_cq_at(real rowvector b, real scalar i)
{
    if (i >= cols(b)) return(0)
    return(b[i] == 96 & b[i + 1] == 34)
}

// The position of the " of the "' that closes the `" at i -- compound
// quotes nest -- or cols(b) + 1 when none does.
real scalar _dash_imm_cq_end(real rowvector b, real scalar i)
{
    real scalar j, n, depth

    n     = cols(b)
    depth = 1
    j     = i + 2
    // j < n, so b[j + 1] is always there.
    while (j < n) {
        if (b[j] == 96 & b[j + 1] == 34) {
            depth++
            j = j + 2
            continue
        }
        if (b[j] == 34 & b[j + 1] == 39) {
            depth--
            if (depth == 0) return(j)
            j = j + 2
            continue
        }
        j++
    }
    return(n + 1)
}

// The next token of the list s, as twoway's parsers read it with gettoken.
// b is ascii(s), read once by the caller; i is where to start, and is moved
// past the token.  mode is how gettoken is called:
//   0  gettoken tok rest : rest                    (quotes stripped)
//   1  gettoken tok rest : rest, quotes
//   2  gettoken tok rest : rest, match(p) quotes   (a clock position)
// Returns the kind of token: 0 none (the list is spent), 1 a word, 2 a
// quoted string, 3 a (group), in mode 2 only.  txt is the token without
// its quotes or outer parentheses -- a group keeps its blanks -- and raw
// is the token as written, for a message.
real scalar _dash_imm_next(string scalar s, real rowvector b, real scalar i,
                           real scalar mode, string scalar txt,
                           string scalar raw)
{
    real scalar n, j, depth

    n = cols(b)
    while (i <= n) {
        if (b[i] != 32) break
        i++
    }
    if (i > n) {
        txt = ""
        raw = ""
        return(0)
    }
    if (b[i] == 34) {
        // "quoted": to the next double quote, or to the end.
        j   = _dash_imm_dq_end(b, i)
        raw = substr(s, i, j - i + 1)
        txt = substr(s, i + 1, j - i - 1)
        i   = j + 1
        return(2)
    }
    if (_dash_imm_cq_at(b, i)) {
        // `"compound"': to the "' that closes this one.
        j   = _dash_imm_cq_end(b, i)
        raw = substr(s, i, j - i + 2)
        txt = substr(s, i + 2, j - i - 2)
        i   = j + 2
        return(2)
    }
    if (mode == 2 & b[i] == 40) {
        // (group): to the parenthesis that closes this one; a quoted string
        // inside it is passed over whole.
        depth = 1
        j     = i + 1
        while (j <= n) {
            if (b[j] == 34) {
                j = _dash_imm_dq_end(b, j) + 1
                continue
            }
            if (_dash_imm_cq_at(b, j)) {
                j = _dash_imm_cq_end(b, j) + 2
                continue
            }
            if (b[j] == 40) depth++
            else if (b[j] == 41) {
                depth--
                if (depth == 0) break
            }
            j++
        }
        if (j > n + 1) j = n + 1
        raw = substr(s, i, j - i + 1)
        txt = substr(s, i + 1, j - i - 1)
        i   = j + 1
        return(3)
    }
    // A word: to the next blank.  A quoted part inside it binds its blanks,
    // as in gettoken -- 2"A B" is one token.
    j = i
    while (j <= n) {
        if (b[j] == 32) break
        if (b[j] == 34) {
            j = _dash_imm_dq_end(b, j) + 1
            continue
        }
        if (_dash_imm_cq_at(b, j)) {
            j = _dash_imm_cq_end(b, j) + 2
            continue
        }
        j++
    }
    if (j > n + 1) j = n + 1
    raw = substr(s, i, j - i)
    txt = raw
    i   = j
    return(1)
}
// _dash_imm_gettoken(s, i, mode, txt, raw), this with ascii(s) read at
// each call, was removed here (WP-26, 24sep2026): only a test called it.
// _dash_imm_records reads the bytes once and calls this.

// s without the blanks (char 32, and nothing else) around it.
string scalar _dash_imm_trim(string scalar s)
{
    real scalar i, j, n

    n = strlen(s)
    i = 1
    while (i <= n) {
        if (substr(s, i, 1) != " ") break
        i++
    }
    j = n
    while (j >= i) {
        if (substr(s, j, 1) != " ") break
        j--
    }
    return(substr(s, i, j - i + 1))
}

// 1 when t is not empty and holds only the bytes a number can be written
// with -- digits, + - . and the letters of the e, d and x forms -- so that
// strtoreal() is never handed a tab, a Unicode digit or anything else it
// might be lenient about.
real scalar _dash_imm_numchars(string scalar t)
{
    real rowvector b
    real scalar    k, c

    if (t == "") return(0)
    b = ascii(t)
    for (k = 1; k <= cols(b); k++) {
        c = b[k]
        if (c >= 48 & c <= 57) continue
        if (c == 43 | c == 45 | c == 46) continue
        if (c >= 97 & c <= 102) continue
        if (c >= 65 & c <= 70) continue
        if (c == 120 | c == 88) continue
        return(0)
    }
    return(1)
}

// 1 when t is a decimal number by its grammar alone, whatever its size:
// [+-] then digits with an optional point and more digits, or a point and
// digits, then optionally e, E, d or D, an optional sign and digits.
real scalar _dash_imm_decimal(string scalar t)
{
    real rowvector b
    real scalar    n, k, nd, ne

    // Mata evaluates both sides of & and &&: every b[k] below is read only
    // once k <= n has been tested on its own.
    b  = ascii(t)
    n  = cols(b)
    k  = 1
    nd = 0
    ne = 0
    if (n == 0) return(0)
    if (b[k] == 43 | b[k] == 45) k++
    while (k <= n) {
        if (b[k] < 48 | b[k] > 57) break
        nd++
        k++
    }
    if (k <= n) {
        if (b[k] == 46) {
            k++
            while (k <= n) {
                if (b[k] < 48 | b[k] > 57) break
                nd++
                k++
            }
        }
    }
    if (nd == 0) return(0)
    if (k > n) return(1)
    if (!anyof((69, 101, 68, 100), b[k])) return(0)
    k++
    if (k <= n) {
        if (b[k] == 43 | b[k] == 45) k++
    }
    while (k <= n) {
        if (b[k] < 48 | b[k] > 57) break
        ne++
        k++
    }
    return(ne > 0 & k > n)
}

// A nonmissing real as a JSON number, at full precision.  %21.0g writes .5
// and -.5, which JSON does not allow, so the zero is put back; its other
// forms -- 3000, -2.5, 1.00000000000000e+21 -- are JSON numbers as written.
// Zero is 0, however it was signed.
string scalar _dash_json_number(real scalar v)
{
    string scalar s

    if (v == 0) return("0")
    s = strtrim(strofreal(v, "%21.0g"))
    if (substr(s, 1, 1) == ".")  s = "0" + s
    if (substr(s, 1, 2) == "-.") s = "-0" + substr(s, 2, .)
    return(s)
}

// _dash_json_number17(v) -- each value of v as a JSON number that reads
// back to the same double, or null for a missing value (WP-29 P0.6).
//
// A function layer's points are drawn as Stata computed them, so every
// digit must survive the trip.  %21.0g does not: in exponent form it keeps
// 15 digits, and 3.3333333333333e-301, -6.66666666666667e-08 and
// -1.46666666666667e+70 read back as other doubles (measured, section 04
// E7).  %24.17g reads back exactly.  It writes .5 and -.5, which JSON does
// not allow, so the zero is put back; 0 is 0 however it was signed; . and
// .a-.z are null (twoway draws a missing value as a gap).
string colvector _dash_json_number17(real colvector v)
{
    string colvector s
    real scalar      i

    s = J(rows(v), 1, "")
    for (i = 1; i <= rows(v); i++) {
        if (v[i] >= .) {
            s[i] = "null"
            continue
        }
        if (v[i] == 0) {
            s[i] = "0"
            continue
        }
        s[i] = strtrim(strofreal(v[i], "%24.17g"))
        if (substr(s[i], 1, 1) == ".")       s[i] = "0" + s[i]
        else if (substr(s[i], 1, 2) == "-.") s[i] = "-0" + substr(s[i], 2, .)
    }
    return(s)
}

// One coordinate, as twoway reads it -- numlist with missingok, then
// stored as a float: a JSON number; "null" for a missing value (. or .a to
// .z, a number past a double's range, or one past a float's); or "" when it
// is no number at all, twoway's "invalid point".  tok is the token as
// gettoken hands it over, quotes stripped.
string scalar _dash_imm_number(string scalar tok)
{
    string scalar t, a, b
    real scalar   v, k

    t = _dash_imm_trim(tok)
    if (t == ".") return("null")
    if (strlen(t) == 2 & substr(t, 1, 1) == ".") {
        if (_dash_ascii_in(substr(t, 2, 1), 97, 122)) return("null")
    }
    // twoway's numlist reads p/q as a range; with one value it is then
    // evaluated as a division: 2/2 and -1/-1 draw at 1, 0/0 is missing
    // (measured 23sep2026 and again for WP-31 C18).  p != q is "invalid
    // point".
    k = strpos(t, "/")
    if (k > 1 & k < strlen(t)) {
        if (strpos(substr(t, k + 1, .), "/") == 0) {
            a = substr(t, 1, k - 1)
            b = substr(t, k + 1, .)
            if (_dash_imm_decimal(a) & _dash_imm_decimal(b)) {
                if (strtoreal(a) == strtoreal(b)) {
                    return(strtoreal(a) == 0 ? "null" : "1")
                }
                return("")
            }
        }
    }
    if (!_dash_imm_numchars(t)) return("")
    v = strtoreal(t)
    if (v < .) {
        // Past float's range the value is missing to twoway and draws
        // nothing.  2^127 - 2^102 is where a double stops rounding to the
        // largest float: 1.7014117837e38 is drawn, 1.7014117839e38 is not
        // (measured).  abs() of minus infinity, which is how strtoreal()
        // reads -1e400, is missing, and so past it too.
        if (abs(v) >= 2^127 - 2^102) return("null")
        return(_dash_json_number(v))
    }
    // strtoreal() reads a decimal number too big for a double as missing,
    // as twoway does; anything else it reads as missing is no number.
    if (_dash_imm_decimal(t)) return("null")
    // A hexadecimal literal whose exponent is +3ff is past c(maxdouble):
    // strtoreal() reads it as missing, and twoway takes it and holds the
    // point as missing (1.0X+3ff, 1.fX+3ff, -1.0X+3ff; WP-31 C18b,
    // measured).  1.0X+400 and any other form strtoreal() refuses are
    // twoway's "invalid point" too.
    if (ustrregexm(t, "^[+-]?1[.][0-9a-fA-F]{1,13}[xX][+]3[fF][fF]$")) {
        return("null")
    }
    return("")
}

// One clock position: a JSON number, or "" when it is not a number from 0
// to 12 -- twoway's "invalid position".
string scalar _dash_imm_clock(string scalar tok)
{
    string scalar t
    real scalar   v

    t = _dash_imm_trim(tok)
    // (1/1) is the clock position 1, twoway's division (WP-31 C18).
    if (_dash_imm_number(t) == "1" & strpos(t, "/")) t = "1"
    if (!_dash_imm_numchars(t)) return("")
    v = strtoreal(t)
    if (v >= . | v < 0 | v > 12) return("")
    return(_dash_json_number(v))
}

// An echo of the user's text, cut at 80 characters so that a refusal or a
// note stays one line however long the text is.
string scalar _dash_imm_echo(string scalar s)
{
    if (ustrlen(s) <= 80) return(s)
    return(usubstr(s, 1, 80) + "...")
}

// The immediate list vals as the JSON array the renderer reads, one record
// per point (w = 2, scatteri) or segment or arrow (w = 4, pci and
// pcarrowi), in twoway's order: the coordinates, then "label",clock when
// either is given (clock null when only the label is).  On a refusal it
// returns "" with err "point", "position" or "none" and bad the token
// refused.  left is what was dropped at the end, as written, and stop why:
// "short", too little for another record, or "empty", a quoted "" where a
// record's last coordinate belongs.  nrec is the number of records read
// and nlab the number with a label that is not empty.
string scalar _dash_imm_records(string scalar vals, real scalar w,
                                string scalar err, string scalar bad,
                                string scalar left, string scalar stop,
                                real scalar nrec, real scalar nlab)
{
    real rowvector   b
    string rowvector c, craw, recs
    real scalar      i, k, kind, lastkind, start, cap
    string scalar    txt, raw, rec, num, lab, clk

    err      = ""
    bad      = ""
    left     = ""
    stop     = ""
    nrec     = 0
    nlab     = 0
    txt      = ""
    raw      = ""
    lastkind = 0
    b        = ascii(vals)
    cap      = 16
    recs     = J(1, cap, "")
    c        = J(1, w, "")
    craw     = J(1, w, "")
    i        = 1

    // The first record's coordinates, read with gettoken: quotes stripped.
    start = i
    for (k = 1; k <= w; k++) {
        lastkind = _dash_imm_next(vals, b, i, 0, txt, raw)
        c[k]     = txt
        craw[k]  = raw
    }
    // twoway's loop: while the record's last coordinate is not empty.
    while (c[w] != "") {
        rec = ""
        for (k = 1; k <= w; k++) {
            num = _dash_imm_number(c[k])
            if (num == "") {
                err = "point"
                bad = craw[k]
                return("")
            }
            rec = rec + (k > 1 ? "," : "") + num
        }
        // An optional (#clockpos), then an optional "label".  Whatever
        // else comes next is the next record's first coordinate.
        lab   = ""
        clk   = ""
        start = i
        kind  = _dash_imm_next(vals, b, i, 2, txt, raw)
        if (kind == 3) {
            clk = _dash_imm_clock(txt)
            if (clk == "") {
                err = "position"
                bad = _dash_imm_trim(txt)
                return("")
            }
            start = i
            kind  = _dash_imm_next(vals, b, i, 1, txt, raw)
        }
        if (kind == 2) {
            lab = txt
            if (lab != "") nlab++
            start = i
            kind  = _dash_imm_next(vals, b, i, 0, txt, raw)
        }
        if (lab != "" | clk != "") {
            if (clk == "") clk = "null"
            rec = rec + "," + char(34) + _dash_json_escape(lab) + char(34) + "," + clk
        }
        if (nrec == cap) {
            recs = recs, J(1, cap, "")
            cap  = 2 * cap
        }
        nrec++
        recs[nrec] = "[" + rec + "]"
        // The next record: its first coordinate is the token just read.
        c[1]    = txt
        craw[1] = raw
        for (k = 2; k <= w; k++) {
            lastkind = _dash_imm_next(vals, b, i, 0, txt, raw)
            c[k]     = txt
            craw[k]  = raw
        }
    }
    left = _dash_imm_trim(substr(vals, start, .))
    if (left != "") stop = (lastkind == 2 ? "empty" : "short")
    if (nrec == 0) {
        err = "none"
        return("")
    }
    return("[" + invtokens(recs[|1 \ nrec|], ",") + "]")
}

// dash.ado's entry point: the records of an immediate list of width w
// (2 for scatteri, 4 for pci and pcarrowi), into the caller's locals.
//   _pci_json     the JSON array, or "" on a refusal
//   _pci_err      "" | "point" | "position" | "none"
//   _pci_bad      the token refused, as written (cut at 80 characters)
//   _pci_left     what was dropped at the end, as written (cut), or ""
//   _pci_hasleft  1 when something was dropped at the end, else 0
//   _pci_stop     why it was: "short" | "empty" | ""
//   _pci_n        the number of records read
//   _pci_nlab     the number of them with a label that is not empty
void _dash_immediate(string scalar vals, real scalar w)
{
    string scalar json, err, bad, left, stop
    real scalar   n, nl

    if (w != 2 & w != 4) {
        errprintf("_dash_immediate: a record is 2 or 4 coordinates\n")
        exit(198)
    }
    err  = ""
    bad  = ""
    left = ""
    stop = ""
    n    = 0
    nl   = 0
    json = _dash_imm_records(vals, w, err, bad, left, stop, n, nl)
    st_local("_pci_json",    json)
    st_local("_pci_err",     err)
    st_local("_pci_bad",     _dash_imm_echo(bad))
    st_local("_pci_left",    _dash_imm_echo(left))
    st_local("_pci_hasleft", strofreal(left != ""))
    st_local("_pci_stop",    stop)
    st_local("_pci_n",       strofreal(n))
    st_local("_pci_nlab",    strofreal(nl))
}

// _dash_pc_immediate(vals), the entry WP-22 gave pcarrowi, was removed
// here (WP-26, 24sep2026): since c036fb6 dash.ado reads pci and pcarrowi
// through _dash_immediate(vals, 4), and only tests called it.

// ============================================================
// 3. OPTION WORDS ARE NOT REWRITTEN HERE
// ============================================================
//
// Stata's -syntax- resolves option keys: dash.ado's declarations carry
// Stata's own measured minimum abbreviations, so option words pass
// through this file untouched.  Two functions that rewrote them were
// removed from here.  dash used to declare every option in lowercase --
// which tells -syntax- to permit NO abbreviation -- and _expand_optkey
// faked abbreviation with a fixed lookup table.  That table accepted
// exactly one short form per option, rejected every other prefix Stata
// accepts, and mapped eight abbreviations to the WRONG option: xl and yl
// went to xline/yline where Stata sends them to xlabel/ylabel, and m, mlc,
// mls, mlp and mlw were likewise mis-routed.  _dash_expand_opts_str, which
// applied it to an option string, was then a verified identity function --
// it returned its input unchanged for nested parentheses, quoted values
// containing commas, repeated whitespace, bare flags and the empty string
// -- so every call site passes the raw option text straight to -syntax-.



// ============================================================
// 3a. SHARED QUOTE STATE MACHINE
// ============================================================
//
// Every scanner below walks the raw command text and must treat the
// inside of a quoted run as opaque -- a parenthesis, a comma or a "||"
// written inside a title is text, not syntax.
//
// There were four hand-written copies of this logic and two of them were
// wrong in the same way: they entered a quote only when the paren depth
// was zero.  So in flat (||) mode a '(' inside a quoted option value
// unbalanced `depth' for the rest of the scan and every later "||"
// stopped being a separator -- measured,
//     dash scatter mpg weight, title("a ( b") name(g) || line mpg weight
// registered ONE plot and reported four options that do not exist, while
// real twoway drew both.  A fifth copy, in _dash_extract_filters, had no
// quote handling at all, so `filter(' inside a title was harvested as a
// filter widget and cut out of the user's text.
//
// This is now the only copy.  Depth is deliberately NOT a parameter: a
// quote is opaque at every depth, which is the entire point.
//
// Handles Stata's two quoting forms:
//     "..."      plain double quotes
//     `"..."'    compound quotes, which may themselves contain '"' and
//                nest: `"a `"b"' c"' is one string
//
// Returns the index just past whatever it consumed, or 0 when the
// character at `i' is not quote-related and the caller should handle it
// itself.  `in_dq' (0/1) and `in_cq' (the compound-quote depth, 0 when
// outside one; callers test it only for being non-zero) are updated in
// place -- Mata passes arguments by reference, verified by probe.
//
real scalar _dash_quote_step(string scalar s,
                             real scalar len,
                             real scalar i,
                             real scalar in_dq,
                             real scalar in_cq)
{
    real scalar c_code

    c_code = ascii(substr(s, i, 1))

    // Inside a compound quote: compound quotes nest, so `in_cq' is the
    // depth -- each `" opens a level and each "' closes one, and the
    // string ends when the depth is back to 0.  A bare '"' within it is
    // ordinary text.  This was an on/off flag, so the first "' ended the
    // outer quote of `"a `"b"' c"' and its own closing "' then opened a
    // plain quote that never closed: title(`"a `"b"' c"') and a nested
    // literal in a qualifier were refused as unterminated, where twoway
    // accepts both (measured 24sep2026, test_parser_integrity.cscript
    // P1B-39..47).  The depth is a count, not a stack, so any nesting
    // costs O(1) per character.
    if (in_cq) {
        if (c_code == 96 & i + 1 <= len & ascii(substr(s, i+1, 1)) == 34) {
            in_cq++
            return(i + 2)
        }
        if (c_code == 34 & i + 1 <= len & ascii(substr(s, i+1, 1)) == 39) {
            in_cq--
            return(i + 2)
        }
        return(i + 1)
    }

    // Inside a plain quote: it ends on the next '"'.
    if (in_dq) {
        if (c_code == 34) {
            in_dq = 0
        }
        return(i + 1)
    }

    // Opening a compound quote -- checked before the plain form so that
    // the '"' of a `" pair is not mistaken for a plain opening quote.
    if (c_code == 96 & i + 1 <= len & ascii(substr(s, i+1, 1)) == 34) {
        in_cq = 1
        return(i + 2)
    }

    // Opening a plain quote.
    if (c_code == 34) {
        in_dq = 1
        return(i + 1)
    }

    return(0)
}


// ============================================================
// 4. COMMA POSITION FINDER
// ============================================================

// Return the character position (1-based) of the first comma at
// depth 0 (outside parens and quotes), or 0 if none found.
real scalar _dash_first_comma_pos(string scalar input) {
    real scalar i, len, depth, in_dq, in_cq, c_code, nxt

    len   = strlen(input)
    depth = 0
    in_dq = 0
    in_cq = 0
    i     = 1

    while (i <= len) {
        // Quoted text is opaque at ANY depth.  This used to enter a quote
        // only when depth was 0, so a '(' inside a quoted option value left
        // the depth counter stuck and a later option comma was mistaken for
        // the top-level one.
        nxt = _dash_quote_step(input, len, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }

        c_code = ascii(substr(input, i, 1))

        if (c_code == 40) {
            depth++
            i++
            continue
        }
        if (c_code == 41 & depth > 0) {
            depth--
            i++
            continue
        }
        if (c_code == 44 & depth == 0) return(i)
        i++
    }
    return(0)
}

void _dash_comma_pos(string scalar input, string scalar out_macro) {
    st_local(out_macro, strofreal(_dash_first_comma_pos(input)))
}


// ============================================================
// 5. PLOT-SEGMENT SPLITTER   (_dash_split_segs)
// ============================================================
//
// The command is read as twoway reads it: split at every "||" outside
// quotes and parentheses into pieces, and each piece is one of
//   (a) a run of parenthesised plots, `(plot) (plot)', with the graph's
//       own [if] [in] [, options] after it;
//   (b) a piece with no plot -- nothing but [if] [in] [, options], or
//       nothing at all -- whose qualifier and options are the graph's;
//   (c) a bare plot, `type args [if] [in] [, options]', one segment, whose
//       options may hold graph-level options too (both are parsed together
//       by the Stata syntax program -- no need to pre-separate them here).
// Measured against twoway 09oct2026 (test_parser.cscript P1A-85): `a || b
// || , title("T")', `(a) || b || , title("T")', `a || , title("T") || b',
// `(a) (b), title("T") || c', `a || b ||', `a || || b' and `a || b || if
// foreign==1' are all rc 0, the qualifier drawing both plots over the 22
// foreign cars.  This splitter used to choose ONE form for the whole
// command from its first character, so a piece with no plot was read as
// a plot -- "unrecognised plot type ','" -- and a bare plot after a
// parenthesised one as stray text; the trailing `|| , opts' form was
// refused for every option.
//
// Sets: _n_segs, _seg_1..N (each with its plot type as its first word),
//       _graph_opts_raw (the options of (a) and (b), joined in order) and
//       _graph_qual_raw (their qualifiers, joined).
//
void _dash_split_segs(string scalar input, | real scalar allow_empty) {
    real   scalar  i, len, depth, in_dq, in_cq, c_code, nxt, p
    real   scalar  seg_start, n_segs, ae
    real   scalar  g_close, g_bars, g_comma
    string scalar  piece, g_rest
    string vector  pieces, segs
    string scalar  graph_opts_raw, graph_qual

    input  = strtrim(input)
    len    = strlen(input)
    pieces = J(1, 0, "")
    segs   = J(1, 0, "")
    graph_opts_raw = ""
    graph_qual     = ""
    // allow_empty (WP-31 A1): 1 from _dash_plot, for every plot command --
    // dash replaces twoway, and twoway alone draws an empty graph, and so do
    // `twoway, title(T)', `twoway if foreign==1' and `twoway ||' (measured
    // 13oct2026, test/fixtures/bare_prefix_truth.json bare.*): no plot is
    // then not an error, and the options and qualifier are the graph's.
    ae = 0
    if (args() >= 2) ae = (allow_empty != 0 & allow_empty < .)

    if (len == 0) {
        if (ae) {
            st_local("_n_segs", "0")
            st_local("_graph_opts_raw", "")
            st_local("_graph_qual_raw", "")
            return
        }
        errprintf("dash: empty plot specification.\n")
        exit(198)
    }

    // ---- || inside the command's first group (WP-35 syn:SD-13) ----
    // twoway draws `(scatter y x || line y x)', with nothing after the
    // group but a comma, as the same plots without the parentheses (rc 0,
    // test/fixtures/command_grammar_truth.json inner.bare, inner.comma),
    // and refuses every other form whose first group holds || at its own
    // depth, r(198): a || piece holding its own comma is "option | not
    // allowed" (inner.piece_comma), options or another group after the
    // group "| invalid name" (inner.title, inner.then_group).  Quotes are
    // opaque; nothing typed is echoed.
    if (substr(input, 1, 1) == "(") {
        depth   = 0
        in_dq   = 0
        in_cq   = 0
        g_close = 0
        g_bars  = 0
        g_comma = 0
        i       = 1
        while (i <= len) {
            nxt = _dash_quote_step(input, len, i, in_dq, in_cq)
            if (nxt) {
                i = nxt
                continue
            }
            c_code = ascii(substr(input, i, 1))
            if (c_code == 40) depth++
            else if (c_code == 41) {
                depth--
                if (depth == 0) {
                    g_close = i
                    break
                }
            }
            else if (depth == 1 & c_code == 124 & i + 1 <= len &
                     ascii(substr(input, i+1, 1)) == 124) {
                g_bars = 1
                i = i + 2
                continue
            }
            else if (depth == 1 & c_code == 44) g_comma = 1
            i++
        }
        if (g_close & g_bars) {
            g_rest = strtrim(substr(input, g_close + 1, .))
            if (!g_comma & (g_rest == "" | g_rest == ",")) {
                input = strtrim(substr(input, 2, g_close - 2))
                len   = strlen(input)
            }
            else if (g_comma) {
                // command_grammar_truth.json inner.piece_comma
                _dash_say("err", "", "option | not allowed", "")
                exit(198)
            }
            else {
                // command_grammar_truth.json inner.title, inner.then_group
                _dash_say("err", "", "| invalid name", "")
                exit(198)
            }
        }
    }

    // ---- split at "||" outside quotes and parentheses ----
    depth     = 0
    in_dq     = 0
    in_cq     = 0
    seg_start = 1
    i         = 1
    while (i <= len) {
        // Quoted text is opaque at ANY depth.  The flat-mode scan once
        // entered a quote only at depth 0, so a '(' inside a quoted option
        // value was counted as a real parenthesis, `depth' never returned
        // to 0, and every later "||" stopped separating.
        nxt = _dash_quote_step(input, len, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }

        c_code = ascii(substr(input, i, 1))

        if (c_code == 40) {
            depth++
        }
        else if (c_code == 41) {
            // A ')' with nothing open: `scatter y x, title("ok"))' and
            // `(a)) (b)' are r(198) in twoway -- measured.  It never leaves
            // `depth' non-zero, so the end-of-scan check cannot catch it.
            if (depth == 0) {
                errprintf("dash: unmatched ')' in the plot specification.\n")
                exit(198)
            }
            depth--
        }
        else if (c_code == 124 & depth == 0 &
                 i + 1 <= len & ascii(substr(input, i+1, 1)) == 124) {
            pieces    = pieces, substr(input, seg_start, i - seg_start)
            seg_start = i + 2
            i         = i + 2
            continue
        }
        i++
    }

    // Reaching the end mid-construct means the specification is
    // malformed:
    //     scatter y x, legend(off || line y2 x      -- unclosed '('
    //     scatter y x, title("oops || line y2 x     -- unterminated '"'
    // Quote first: an unterminated quote also leaves `depth' stuck, and
    // naming the parenthesis sends the user after the wrong character.
    if (in_dq | in_cq) {
        errprintf("dash: unterminated quotation in the plot specification.\n")
        exit(198)
    }
    // twoway's own line, with no line after (WP-49 plot:PT-7;
    // refusal_line_truth.json sd12.Q14: "(scatter mpg weight", and
    // legend(off || line ... and title(a alike, measured 12nov2026).
    if (depth != 0) {
        errprintf("parentheses do not balance\n")
        exit(198)
    }
    pieces = pieces, substr(input, seg_start, .)

    // ---- read each piece ----
    // An empty piece -- `a || || b', a leading or a trailing `||' -- adds
    // nothing, as in twoway.
    for (p = 1; p <= cols(pieces); p++) {
        piece = strtrim(pieces[p])
        if (piece == "") continue
        if (_dash_piece_is_bare(piece)) {
            segs = segs, piece
        }
        else {
            _dash_split_groups(piece, segs, graph_opts_raw, graph_qual)
        }
    }

    n_segs = cols(segs)
    if (n_segs == 0 & !ae) {
        errprintf("dash: no plot specifications found.\n")
        exit(198)
    }

    // Store results in caller's local-macro environment
    st_local("_n_segs", strofreal(n_segs))
    for (i = 1; i <= n_segs; i++) {
        st_local("_seg_" + strofreal(i), segs[i])
    }
    st_local("_graph_opts_raw", strtrim(graph_opts_raw))
    // The qualifier written after the parenthesised groups or in a piece
    // with no plot, every piece of it.  A qualifier in a bare plot is that
    // plot's own (twoway draws `scatter y x || line y x if foreign==1' as
    // 74 points and a line through 22), and stays in its segment.
    st_local("_graph_qual_raw", strtrim(graph_qual))
}

// 1 when a trimmed, non-empty piece of the command is a bare plot -- it
// begins with neither '(', nor ',', nor an if/in qualifier -- and 0 when
// it is a run of plot groups or a piece with no plot.  The qualifier word
// is lower case, as -syntax- reads it, with a blank after it or, for `if',
// a parenthesis: twoway takes `if(foreign==1)'.  No plot type is named if
// or in, and `ifx' is a word.
real scalar _dash_piece_is_bare(string scalar piece) {
    real scalar   c1, qnext
    string scalar qword

    c1 = ascii(substr(piece, 1, 1))
    if (c1 == 40 | c1 == 44) return(0)
    qword = substr(piece, 1, 2)
    qnext = (strlen(piece) >= 3 ? ascii(substr(piece, 3, 1)) : 32)
    if (qword == "if" & (qnext == 32 | qnext == 9 | qnext == 40)) return(0)
    if (qword == "in" & (qnext == 32 | qnext == 9)) return(0)
    return(1)
}

// One piece of the command that is not a bare plot (_dash_piece_is_bare):
// its parenthesised plots are appended to segs, its qualifier to qual and
// the text after its top-level comma to gopts, each joined with a blank.
// The piece holds no top-level "||" and its quotes and parentheses are
// balanced -- _dash_split_segs has checked both -- so nothing is left open
// at its end.
void _dash_split_groups(string scalar s,
                        string vector segs,
                        string scalar gopts,
                        string scalar qual)
{
    real   scalar i, len, depth, in_dq, in_cq, c_code, nxt
    real   scalar seg_start, qual_seen, qual_start, qnext
    string scalar seg_text, qword, go

    len        = strlen(s)
    depth      = 0
    in_dq      = 0
    in_cq      = 0
    seg_start  = 0
    qual_seen  = 0
    qual_start = 0
    i          = 1

    while (i <= len) {
        // Quoted text is opaque at any depth.
        nxt = _dash_quote_step(s, len, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }

        c_code = ascii(substr(s, i, 1))

        // ---- inside an if/in qualifier written after the plot groups or
        // in a piece with no plot ----
        // twoway applies such a qualifier to every plot (measured:
        // `(scatter y x) (line y x) if foreign==1' draws the 22 foreign
        // cars in both, and so does `scatter y x || line y x || if
        // foreign==1'), and allows one `if' and one `in' in all ("multiple
        // global if's not allowed").  It is collected here, whole, into
        // qual, and _dash_plot reads it with -syntax- as the graph's own
        // qualifier.  Inside the qualifier a parenthesis is the
        // expression's -- `if inlist(rep78,3,4)' opens no plot group; it
        // ends at a comma outside its parentheses, or at the end.  A plot
        // group written after it stays part of its text, where -syntax-
        // refuses it with twoway's own "invalid '('".
        if (qual_seen) {
            if (c_code == 40) depth++
            else if (c_code == 41) depth--
            else if (depth == 0 & c_code == 44) {
                qual      = qual + " " + strtrim(substr(s, qual_start, i - qual_start))
                qual_seen = 0
                // Back to the comma: the branch below reads the options.
                continue
            }
            i++
            continue
        }

        if (c_code == 40 & depth == 0) {
            seg_start = i + 1
            depth     = 1
        }
        else if (c_code == 40) depth++
        else if (c_code == 41) {
            depth--
            if (depth == 0 & seg_start > 0) {
                seg_text = strtrim(substr(s, seg_start, i - seg_start))
                if (seg_text != "") segs = segs, seg_text
                seg_start = 0
            }
        }
        else if (c_code == 44 & depth == 0) {
            // top-level comma after the () groups -> graph opts
            go = strtrim(substr(s, i + 1, .))
            // A graph option always begins with its own name, so a '('
            // opening this text is a plot group written after the
            // comma.  twoway returns r(198) for `(a), (b)' and for `a ||
            // , (b)'; dash used to swallow the group into the option
            // string.
            if (go != "" & ascii(substr(go, 1, 1)) == 40) {
                errprintf(
                  "dash: a plot group may not follow the graph-option comma.\n")
                errprintf(
                  "      Write every plot before the comma: (plot1) (plot2), <options>\n")
                exit(198)
            }
            gopts = gopts + " " + go
            return
        }
        else if (depth == 0 & c_code != 32 & c_code != 9) {
            // A top-level if/in qualifier may follow the plot groups or
            // open a piece with no plot:
            //     (scatter y x) if foreign==1, title("T")
            //     scatter y x || line y x || if foreign==1, title("T")
            // the word in lower case, as Stata's own -syntax- reads it
            // (`IF foreign==1' is r(198) in twoway), with a blank or, for
            // `if', a parenthesis after it (measured rc 0: `(scatter mpg
            // weight) if(foreign==1)' draws the 22 foreign cars).  It is
            // read by the branch above, from the word on.
            qword = substr(s, i, 2)
            qnext = (i + 2 <= len ? ascii(substr(s, i+2, 1)) : 32)
            if ((qword == "if" & (qnext == 32 | qnext == 9 | qnext == 40)) |
                (qword == "in" & (qnext == 32 | qnext == 9))) {
                qual_seen  = 1
                qual_start = i
                i = i + 2
                continue
            }

            // twoway's _parse expand: text after a group, to the end of
            // the piece, is one more plot (WP-35 syn:SD-1;
            // command_grammar_truth.json group.*): `(a) line y x' draws
            // two plots, its comma and options belonging to that plot as
            // a bare plot's do.  It is read as any bare plot is, so `(a)
            // junk (b)' is "junk is not a twoway plot type", r(198), and
            // `(a) | (b)' "| is not a twoway plot type", as in twoway.
            seg_text = strtrim(substr(s, i, .))
            segs = segs, seg_text
            return
        }
        i++
    }

    // A qualifier that runs to the end of the piece.
    if (qual_seen) {
        qual = qual + " " + strtrim(substr(s, qual_start, .))
    }
}


// ============================================================
// 6. JSON VARIABLE EXTRACTOR  (used by _dash_prepare_spec and
//    _dash_render_immediate)
// ============================================================
//
// Scans a plot-spec JSON string and collects all "yvar", "xvar",
// "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var" values,
// and the option-named variables "mlabel", "mlabvposition" (WP-30
// P1.24: a variable of per-row clock positions), "colorvar" and "wexp" (the
// weight variable, WP-18: it lives inside "options" and must reach the
// data JSON on the immediate route and the build route alike), into a
// space-separated varlist stored in out_macro.
//
void _dash_extract_vars(string scalar json_str, string scalar out_macro) {
    string rowvector keys
    string scalar    found, varlist, val
    real scalar      pos, endpos, orig_pos, local_pos, k

    // Include "colorvar" so the variable referenced by colorvar() is added to
    // the jsonio varlist; without this, foreign/etc. is missing from the data
    // JSON and value labels never reach the Python renderer.  recast_hi
    // is the second bound of a range source drawn as a yx type (WP-46
    // RH-3): exported so its extent and title can be drawn.
    keys    = (char(34)+"yvar"+char(34)+":",   char(34)+"xvar"+char(34)+":",  char(34)+"var"+char(34)+":",
               char(34)+"yvar1"+char(34)+":", char(34)+"yvar2"+char(34)+":",
               char(34)+"y1var"+char(34)+":", char(34)+"x1var"+char(34)+":", char(34)+"y2var"+char(34)+":", char(34)+"x2var"+char(34)+":",
               char(34)+"mlabel"+char(34)+":",
               char(34)+"mlabvposition"+char(34)+":",
               char(34)+"colorvar"+char(34)+":",
               char(34)+"wexp"+char(34)+":",
               char(34)+"zvar"+char(34)+":",
               char(34)+"recast_hi"+char(34)+":")
    varlist = ""

    for (k = 1; k <= cols(keys); k++) {
        pos = 1
        while (pos <= strlen(json_str)) {
            orig_pos  = pos
            local_pos = strpos(substr(json_str, orig_pos, .), keys[k])
            if (local_pos == 0) break
            pos = orig_pos + local_pos - 1 + strlen(keys[k])
            // skip whitespace and colon
            while (pos <= strlen(json_str) &
                   (substr(json_str, pos, 1) == " " |
                    substr(json_str, pos, 1) == char(9))) pos++
            if (pos <= strlen(json_str) & substr(json_str, pos, 1) == char(34)) {
                pos++
                endpos = pos
                while (endpos <= strlen(json_str) &
                       substr(json_str, endpos, 1) != char(34)) endpos++
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


// ============================================================
// 6a. hover() VARIABLE EXTRACTOR (WP-29 P0.10; used by
//     _dash_prepare_spec and _dash_render_immediate)
//     _dash_extract_hover_vars(json_str, out_macro, bad_macro, why_macro)
//
// The variables a graph's hover() names, each once, in the order first
// written, blank-separated, into the caller's local out_macro.  hover()
// is read as the filter refusal reads it -- _dash_json_get_str: the
// first "hover":" key, its escapes decoded; a title holding that text
// carries its quotes escaped and never matches -- and split as the
// renderer splits it (_dash_blank_words).  Each word must be a Stata name
// (_dash_is_varname) and the exact name of a variable in memory
// (_st_varindex with no abbreviation: dash.ado stored the full names at
// registration, OV-110).  The first word that is not stops the read:
// bad_macro gets it, at most 80 characters (the first 77 and "..."),
// why_macro "name" (not a Stata name) or "var" (no such variable), and
// out_macro stays empty.  No word is ever run as code.
// _dash_extract_vars is not used: it reads a raw value as ONE name and
// decodes and checks nothing.
// ============================================================
void _dash_extract_hover_vars(string scalar json_str,
                              string scalar out_macro,
                              string scalar bad_macro,
                              string scalar why_macro)
{
    string rowvector words
    string scalar    w, out
    real scalar      i
    transmorphic     seen

    st_local(out_macro, "")
    st_local(bad_macro, "")
    st_local(why_macro, "")
    _dash_json_get_str(json_str, "hover", "_dehv_raw")
    words = _dash_blank_words(st_local("_dehv_raw"))
    st_local("_dehv_raw", "")
    seen = asarray_create()
    out  = ""
    for (i = 1; i <= cols(words); i++) {
        w = words[i]
        if (asarray_contains(seen, w)) continue
        if (!_dash_is_varname(w)) {
            st_local(bad_macro, ustrlen(w) > 80 ? usubstr(w, 1, 77) + "..." : w)
            st_local(why_macro, "name")
            return
        }
        if (_st_varindex(w, 0) >= .) {
            st_local(bad_macro, w)
            st_local(why_macro, "var")
            return
        }
        asarray(seen, w, 1)
        out = out + (out == "" ? "" : " ") + w
    }
    st_local(out_macro, out)
}


// ============================================================
// 6b. QUALIFIER / FACET VARIABLE EXTRACTOR
//     _dash_extract_qual_vars(json_str, out_macro)
//
// Scans a plot-spec JSON string and collects Stata variable names
// referenced only in graph-level qualifier or faceting fields
// (which _dash_extract_vars never looks at):
//
//   "by"      -- each token in the varlist (before the first comma)
//   "if_expr" -- identifier tokens of the Stata expression
//
// A token is a run of the bytes a Stata name is made of -- ASCII
// letters, digits and _, and every byte of 128 or more, which is part
// of a Unicode letter -- that does not start with a digit and, in an
// if, is not a Python keyword/constant.  Callers in dash.ado
// should use `capture confirm variable' to discard any tokens
// that are not real dataset variables (e.g. string literals that
// happened to look like identifiers in the expression).
//
// Stores the names found -- each once, in the order first seen, the
// "by" names before the "if_expr" names -- as a space-separated list
// in the caller's local out_macro.
// ============================================================

// _dash_qual_str(b, pos) -- one JSON string value, its escapes blanked.
//
// b holds the bytes of the whole JSON text, as ascii() gives them, and
// b[pos] is the value's opening quote.  Returns the value with every
// escape, and any raw control byte, replaced by blanks, and leaves pos one
// past the closing quote -- past the end of b when there is none.
//
// An escape is found by its byte, 92.  This reader used to compare each
// character with the Mata literal "\\", which is TWO characters --
// measured, strlen("\\") is 2 and "\\" == char(92) is 0 -- so no escape
// was ever stepped over: the backslash of \" was kept and the quote after
// it ended the value, and every name after the first string literal of a
// qualifier was lost.  Measured 23sep2026 at ad13a0f: for
//     make != "AMC Concord" & foreign == 1
// only make was returned, foreign was not exported, and the saved page and
// the served app each warned "if_expr filter skipped" and drew all 74 cars
// instead of the 22 the qualifier selects.
//
// Each escape becomes blanks, never nothing.  JSON escapes a quote, a
// backslash, a slash or a control character, none of which can be part of
// a Stata name, so the words on either side of one stay two words.
// \uXXXX is six bytes and every other escape two; a \u that four hex
// digits do not follow counts as two, so the blanks never cover a quote.
//
// Linear in the length of the value: its bytes are read once and blanked
// in place.  The value used to be grown one character at a time, which is
// quadratic -- measured 48.6 s for a value of 1,000,000 characters -- and
// only the early stop above kept a long escaped value from paying for it.
string scalar _dash_qual_str(real rowvector b, real scalar pos)
{
    real rowvector v, h
    real scalar    n, i, e, m, j

    n = cols(b)
    // The closing quote is the first byte 34 no escape takes.  The hex
    // digits of \uXXXX are never a quote or a backslash, so stepping two
    // bytes at every backslash finds it.
    i = pos + 1
    while (i <= n) {
        if (b[i] == 34) break
        i = i + (b[i] == 92 ? 2 : 1)
    }
    e   = min((i, n + 1))
    m   = e - pos - 1
    j   = pos + 1
    pos = e + 1
    if (m <= 0) return("")
    v = b[|j \ e - 1|]

    j = 1
    while (j <= m) {
        if (v[j] == 92 & j < m) {
            if (v[j + 1] == 117 & j + 5 <= m) {
                h = v[|j + 2 \ j + 5|]
                if (all((h :>= 48 :& h :<= 57) :| (h :>= 65 :& h :<= 70) :|
                        (h :>= 97 :& h :<= 102))) {
                    v[|j \ j + 5|] = J(1, 6, 32)
                    j = j + 6
                    continue
                }
            }
            v[|j \ j + 1|] = (32, 32)
            j = j + 2
            continue
        }
        if (v[j] < 32) v[j] = 32
        j++
    }
    return(char(v))
}

void _dash_extract_qual_vars(string scalar json_str,
                              string scalar out_macro) {
    string rowvector keys, reserved, toks, found
    string scalar    val
    real rowvector   b, keep, v, sep
    real matrix      sp
    real scalar      pos, local_pos, orig_pos, n, k, t, comma_pos, c1
    transmorphic     seen

    // Python expression keywords/constants that are not Stata variable names.
    reserved = ("True", "False", "None", "nan", "NaN", "inf",
                "and",  "or",    "not",  "in",  "is")

    // "by" first, then "if_expr": the order the names are listed in.
    keys = (char(34) + "by"      + char(34) + ":",
            char(34) + "if_expr" + char(34) + ":")

    b = ascii(json_str)
    n = cols(b)

    // Each name is listed once.  Whether it has been is a hash lookup; it
    // was a search of the whole list so far for every word, which is
    // quadratic in the number of words.
    seen  = asarray_create()
    found = J(1, 0, "")

    for (k = 1; k <= cols(keys); k++) {
        pos = 1
        while (pos <= n) {
            orig_pos  = pos
            local_pos = strpos(substr(json_str, orig_pos, .), keys[k])
            if (local_pos == 0) break
            pos = orig_pos + local_pos - 1 + strlen(keys[k])
            // Skip optional whitespace before the opening quote.
            while (pos <= n) {
                if (b[pos] != 32 & b[pos] != 9) break
                pos++
            }
            if (pos > n) break
            if (b[pos] != 34) continue
            if (k == 2) {
                // An if: the names outside its string literals, and only
                // those.  Every name-like word of the value was taken, a
                // literal's included, and the callers keep each word
                // `confirm variable' accepts -- an abbreviation among them
                // -- so `if make != "d"' exported displacement, and a KPI's
                // `if make != "t h"' headroom, into the data the renderer
                // reads, where each counted against the embedded-data
                // limit (measured 24sep2026; test_qualifier_literals.cscript
                // QL-21).  The value is decoded, so the scanner sees the
                // literal's quotes the escapes stood for.
                val = _dash_qual_json_text(b, pos)
                sp  = _dash_qual_name_spans(val)
                if (rows(sp) == 0) continue
                toks = J(1, rows(sp), "")
                for (t = 1; t <= rows(sp); t++) {
                    toks[t] = substr(val, sp[t, 1], sp[t, 2])
                }
                keep = J(1, cols(toks), 0)
                for (t = 1; t <= cols(toks); t++) {
                    if (anyof(reserved, toks[t])) continue
                    if (asarray_contains(seen, toks[t])) continue
                    asarray(seen, toks[t], 1)
                    keep[t] = 1
                }
                if (any(keep)) found = found, select(toks, keep)
                continue
            }
            val = _dash_qual_str(b, pos)
            if (k == 1) {
                // Only tokenize before the first comma to avoid option
                // keywords such as "cols", "total", "missing" in
                // by(varlist, opts).
                comma_pos = strpos(val, ",")
                if (comma_pos > 0) val = substr(val, 1, comma_pos - 1)
            }
            // Every byte that cannot be part of a Stata name becomes a
            // blank: the operators and punctuation of an if, and whatever
            // separates the names of a by().  That includes ~, Stata's
            // logical not beside !: the list of operators this replaced had
            // ~= and no ~, so `if ~foreign' named no variable and foreign
            // was not exported (measured 23sep2026).  A byte of 128 or more
            // is kept: it is part of a UTF-8 character, and a Stata name
            // may hold Unicode letters -- an if on a variable named with an
            // e-acute and "tranger" named no variable either, the pattern
            // this replaced being ASCII.  The callers confirm that each name
            // exists.
            v = ascii(val)
            if (cols(v) == 0) continue
            sep = (v :< 128) :& !((v :>= 48 :& v :<= 57) :| (v :>= 65 :& v :<= 90) :|
                                  (v :>= 97 :& v :<= 122) :| (v :== 95))
            toks = tokens(char(v :* !sep + 32 :* sep))
            if (cols(toks) == 0) continue
            keep = J(1, cols(toks), 0)
            for (t = 1; t <= cols(toks); t++) {
                // A name does not start with a digit, so numbers are passed
                // over; in an if, so are Python's reserved words.
                c1 = ascii(substr(toks[t], 1, 1))
                if (c1 >= 48 & c1 <= 57) continue
                if (k == 2) {
                    if (anyof(reserved, toks[t])) continue
                }
                if (asarray_contains(seen, toks[t])) continue
                asarray(seen, toks[t], 1)
                keep[t] = 1
            }
            // Only when something is kept: select() of a single word that
            // is not is 0 x 1, which cannot be joined to a row.
            if (any(keep)) found = found, select(toks, keep)
        }
    }

    st_local(out_macro, invtokens(found))
}


// ------------------------------------------------------------
// _dash_qual_json_text(b, pos) -- one JSON string value, decoded.
//
// As _dash_qual_str, but each escape becomes the character it stands for,
// so that a qualifier's string literals -- whose quotes the registry holds
// as \" and whose compound quotes' backtick and apostrophe as ` and
// ' -- can be told from the names around them.  b holds the bytes of
// the whole JSON text and b[pos] the value's opening quote; pos is left one
// past the closing quote.  A \uXXXX that is half of a surrogate pair, which
// is no character, becomes a blank.  Linear: the text is never longer than
// its escaped form, so it is written into a vector of that length.
// ------------------------------------------------------------
string scalar _dash_qual_json_text(real rowvector b, real scalar pos)
{
    real rowvector v, o, h, u
    real scalar    n, i, e, m, j, k, c, cp, d

    n = cols(b)
    i = pos + 1
    while (i <= n) {
        if (b[i] == 34) break
        i = i + (b[i] == 92 ? 2 : 1)
    }
    e   = min((i, n + 1))
    m   = e - pos - 1
    j   = pos + 1
    pos = e + 1
    if (m <= 0) return("")
    v = b[|j \ e - 1|]
    o = J(1, m, 32)
    k = 0
    j = 1
    while (j <= m) {
        c = v[j]
        if (c == 92 & j < m) {
            c = v[j + 1]
            if (c == 117 & j + 5 <= m) {
                h = v[|j + 2 \ j + 5|]
                if (all((h :>= 48 :& h :<= 57) :| (h :>= 65 :& h :<= 70) :|
                        (h :>= 97 :& h :<= 102))) {
                    cp = 0
                    for (d = 1; d <= 4; d++) {
                        cp = cp * 16 + (h[d] <= 57 ? h[d] - 48 :
                                        (h[d] <= 70 ? h[d] - 55 : h[d] - 87))
                    }
                    if (cp < 128) {
                        o[++k] = cp
                    }
                    else if (cp >= 55296 & cp <= 57343) {
                        o[++k] = 32
                    }
                    else {
                        u = ascii(uchar(cp))
                        o[|k + 1 \ k + cols(u)|] = u
                        k = k + cols(u)
                    }
                    j = j + 6
                    continue
                }
            }
            if      (c == 98)  o[++k] = 8
            else if (c == 102) o[++k] = 12
            else if (c == 110) o[++k] = 10
            else if (c == 114) o[++k] = 13
            else if (c == 116) o[++k] = 9
            else               o[++k] = c
            j = j + 2
            continue
        }
        o[++k] = c
        j++
    }
    if (k == 0) return("")
    return(char(o[|1 \ k|]))
}


// ------------------------------------------------------------
// _dash_qual_name_spans(s) -- where the names of an if-expression are.
//
// One row per name, (first byte, length), in order.  A name is one Stata
// would read as a variable: outside every string literal, plain ("...",
// which ends at the next double quote) or compound (`"..."', which may
// nest); not a function -- a name followed at once by "(": measured
// 24sep2026, `count if abs (mpg) > 20' is "abs not found", r(111), so a
// blank makes it a name again; not next to a period -- the letter of the
// missing value .a, a time-series operator's L. and its operand; and not
// one of the names Stata reserves, which are never variables (_n, _N,
// _pi, _b, _se, ...).  A number, with the letters and periods after its
// first digit (3e3, 3.5e+3), is passed over.  A byte of 128 or more is part
// of a name: Stata names may hold Unicode letters.  Two passes, counting
// then writing, so no row is appended one at a time: linear in s.
// ------------------------------------------------------------
real matrix _dash_qual_name_spans(string scalar s)
{
    real rowvector   b
    real matrix      sp
    real scalar      n, i, j, c, depth, k, isname, pass
    string rowvector reserved

    reserved = ("_all", "_b", "_coef", "_cons", "_n", "_N", "_pi",
                "_pred", "_rc", "_se", "_skip", "byte", "double",
                "float", "int", "long", "strL", "if", "in", "using",
                "with")
    b  = ascii(s)
    n  = cols(b)
    sp = J(0, 2, .)
    for (pass = 1; pass <= 2; pass++) {
        k = 0
        i = 1
        while (i <= n) {
            c = b[i]
            if (c == 96 & i < n) {
                if (b[i + 1] == 34) {
                    depth = 1
                    i = i + 2
                    while (i <= n) {
                        if (depth == 0) break
                        if (b[i] == 96 & i < n) {
                            if (b[i + 1] == 34) {
                                depth++
                                i = i + 2
                                continue
                            }
                        }
                        if (b[i] == 34 & i < n) {
                            if (b[i + 1] == 39) {
                                depth--
                                i = i + 2
                                continue
                            }
                        }
                        i++
                    }
                    continue
                }
            }
            if (c == 34) {
                i++
                while (i <= n) {
                    if (b[i] == 34) break
                    i++
                }
                i++
                continue
            }
            if (c >= 48 & c <= 57) {
                while (i <= n) {
                    c = b[i]
                    if (!(c >= 128 | (c >= 48 & c <= 57) |
                          (c >= 65 & c <= 90) | (c >= 97 & c <= 122) |
                          c == 95 | c == 46)) break
                    i++
                }
                continue
            }
            if (c >= 128 | (c >= 65 & c <= 90) | (c >= 97 & c <= 122) |
                c == 95) {
                j = i
                while (j <= n) {
                    c = b[j]
                    if (!(c >= 128 | (c >= 48 & c <= 57) |
                          (c >= 65 & c <= 90) | (c >= 97 & c <= 122) |
                          c == 95)) break
                    j++
                }
                isname = 1
                if (i > 1) {
                    if (b[i - 1] == 46) isname = 0
                }
                if (j <= n) {
                    if (b[j] == 40 | b[j] == 46) isname = 0
                }
                if (isname) {
                    if (anyof(reserved, substr(s, i, j - i))) isname = 0
                }
                if (isname) {
                    k++
                    if (pass == 2) sp[k, .] = (i, j - i)
                }
                i = j
                continue
            }
            i++
        }
        if (pass == 1) sp = J(k, 2, .)
    }
    return(sp)
}


// ------------------------------------------------------------
// _dash_qual_expand(s) -- an if-expression with each variable it
// abbreviates written out.
//
// As Stata reads it against the data in memory, which is the data it was
// just evaluated against when a graph or KPI is registered: `dis > 100' is
// `displacement > 100' (count if dis > 100 is 60, measured 24sep2026).  The
// renderer evaluates a qualifier against the exported columns, which carry
// full names, so an abbreviation named no column there: the qualifier was
// skipped with a warning and every row drawn (test_qualifier_literals
// QL-22).  Only the names _dash_qual_name_spans finds are read; a name that
// is no variable -- a scalar, a name `set varabbrev off' leaves unexpanded
// -- and every string literal are left as typed.  The pieces are joined
// once, at the end: adding each to a growing string would be quadratic.
// ------------------------------------------------------------
string scalar _dash_qual_expand(string scalar s)
{
    real matrix      sp
    real scalar      k, m, idx, from, abbrev
    string rowvector part

    sp     = _dash_qual_name_spans(s)
    abbrev = (c("varabbrev") == "on")
    part   = J(1, 2 * rows(sp) + 1, "")
    m      = 0
    from   = 1
    for (k = 1; k <= rows(sp); k++) {
        idx = _st_varindex(substr(s, sp[k, 1], sp[k, 2]), abbrev)
        if (idx < .) {
            part[++m] = substr(s, from, sp[k, 1] - from)
            part[++m] = st_varname(idx)
            from      = sp[k, 1] + sp[k, 2]
        }
    }
    part[++m] = substr(s, from, .)
    return(invtokens(part[|1 \ m|], ""))
}


// ============================================================
// 6b. QUALIFIERS, EVALUATED IN STATA
//
// Every qualifier dash.ado writes -- a plot's, a graph's, a KPI's; its if
// and its in together -- is evaluated in Stata, once, against the data as
// they are exported, and travels as a 0/1 byte column named __dashq<k>.
// The spec names that column ("qual_col") and carries no qualifier text,
// so neither renderer translates a qualifier dash.ado wrote.  They used to
// translate each into a pandas query, which read a missing value, a
// subscript, a function, a date and a dozen smaller things otherwise than
// Stata (BUGS.md; test_qualifier_in_stata.cscript).
//
// The table of distinct qualifiers lives in two Mata externals for the
// length of one export: _dash_qual_reset() empties it, _dash_qual_take()
// and _dash_qual_rewrite() fill it, _dash_qual_export() hands it to the
// ado program that evaluates it (_dash_qual_gen).  Identical (if, in)
// pairs share one column.
// ============================================================

void _dash_qual_reset()
{
    external transmorphic scalar _dash_qual_tab
    external string matrix       _dash_qual_list

    // The fourth part of each key is the frame the pair is evaluated in
    // (WP-33 33-07, _dash_frame_key_now); "" on a build of one frame.
    _dash_qual_tab  = asarray_create("string", 4)
    _dash_qual_list = J(0, 4, "")
    // Every export starts on one frame: a build of several sets its own
    // keys after this (_dash_frame_set, _dash_frame_set_all), so a build
    // that stopped half way leaves nothing for the next export.
    _dash_frame_set("")
    _dash_frame_set_all(0)
}


// _dash_qual_refusal(ifx, inx) -- "" when the pair is one dash evaluates,
// else why not.
//
// dash.ado stores a qualifier only after -syntax- has read it, so these
// are the checks a registry set by hand needs: _dash_qual_gen puts the if
// inside parentheses and the in after the keyword on a command line, and
// neither may reach past its place.  The in is Stata's range -- # or #/#,
// each [-]digits, f or l -- and nothing else; the if keeps every bracket
// it opens inside the parentheses around it, holds no control byte, and
// no backtick or dollar sign outside its string literals, where Stata
// would already have expanded one when the graph was registered.
string scalar _dash_qual_refusal(string scalar ifx, string scalar inx)
{
    real rowvector b
    real scalar    n, i, c, depth, lit

    if (strtrim(inx) != "") {
        if (!regexm(inx, "^[ ]*(-?[0-9]+|[fFlL])[ ]*(/[ ]*(-?[0-9]+|[fFlL])[ ]*)?$")) {
            return("its in range is not one Stata reads")
        }
    }
    b     = ascii(ifx)
    n     = cols(b)
    depth = 0
    i     = 1
    while (i <= n) {
        c = b[i]
        if (c == 96 & i < n) {
            if (b[i + 1] == 34) {
                lit = 1
                i   = i + 2
                while (i <= n) {
                    if (lit == 0) break
                    if (b[i] == 96 & i < n) {
                        if (b[i + 1] == 34) {
                            lit++
                            i = i + 2
                            continue
                        }
                    }
                    if (b[i] == 34 & i < n) {
                        if (b[i + 1] == 39) {
                            lit--
                            i = i + 2
                            continue
                        }
                    }
                    if (b[i] < 32) return("it holds a control character")
                    i++
                }
                if (lit != 0) return("a string literal in it is not closed")
                continue
            }
        }
        if (c == 34) {
            i++
            while (i <= n) {
                if (b[i] == 34) break
                if (b[i] < 32) return("it holds a control character")
                i++
            }
            if (i > n) return("a string literal in it is not closed")
            i++
            continue
        }
        if (c < 32 & c != 9) return("it holds a control character")
        if (c == 96 | c == 36) return("it holds a macro character outside a string literal")
        if (c == 40 | c == 91) depth++
        if (c == 41 | c == 93) {
            depth--
            if (depth < 0) return("it closes a parenthesis it did not open")
        }
        i++
    }
    if (depth != 0) return("it leaves a parenthesis open")
    return("")
}


// _dash_qual_take(ifx, inx, errmacro, name_them) -- the column that holds
// the pair, "" for none.  A pair _dash_qual_refusal refuses puts its reason
// in the caller's local errmacro and takes no column.  With name_them 0
// the pair is checked and no column is made: a dashboard with no data.
// The pair is evaluated in the data's order (a KPI's, or a graph's with no
// by()); _dash_qual_take_by names another order.
string scalar _dash_qual_take(string scalar ifx, string scalar inx,
                              string scalar errmacro, real scalar name_them)
{
    return(_dash_qual_take_by(ifx, inx, "", errmacro, name_them))
}


// _dash_qual_take_by(ifx, inx, order, errmacro, name_them) -- as
// _dash_qual_take, for the pair evaluated with the data sorted, stably, on
// the variables order names ("" for the data's own order): a by() graph's
// qualifier, as twoway evaluates it (_dash_qual_rewrite).  The same pair in
// two orders is two columns.
string scalar _dash_qual_take_by(string scalar ifx, string scalar inx,
                                 string scalar order, string scalar errmacro,
                                 real scalar name_them)
{
    external transmorphic scalar _dash_qual_tab
    external string matrix       _dash_qual_list
    string rowvector key
    string scalar    why
    real scalar      k

    // On a build of several frames (WP-33 33-07) the empty pair takes a
    // column too: 1 on its frame's rows, 0 on every other frame's.
    if (strtrim(ifx) == "" & strtrim(inx) == "" & !_dash_frame_all_now()) return("")
    why = _dash_qual_refusal(ifx, inx)
    if (why != "") {
        st_local(errmacro, why)
        return("")
    }
    if (!name_them) return("")
    key = (ifx, inx, order, _dash_frame_key_now())
    if (asarray_contains(_dash_qual_tab, key)) {
        return(_dash_col_pfx() + "q" + strofreal(asarray(_dash_qual_tab, key)))
    }
    if (rows(_dash_qual_list) >= 99999) {
        st_local(errmacro, "the dashboard holds more distinct qualifiers than dash evaluates (99,999)")
        return("")
    }
    _dash_qual_list = _dash_qual_list \ key
    k = rows(_dash_qual_list)
    asarray(_dash_qual_tab, key, k)
    return(_dash_col_pfx() + "q" + strofreal(k))
}


// _dash_qual_blank_lits(s) -- s with the text inside each of its string
// literals, "..." and `"..."' (nested), made blanks, so what is left is
// the expression's own words.  A literal left open blanks the rest.
string scalar _dash_qual_blank_lits(string scalar s)
{
    real rowvector b
    real scalar    n, i, lit

    b = ascii(s)
    n = cols(b)
    i = 1
    while (i <= n) {
        if (b[i] == 96 & i < n) {
            if (b[i + 1] == 34) {
                lit = 1
                i   = i + 2
                while (i <= n & lit > 0) {
                    if (b[i] == 96 & i < n) {
                        if (b[i + 1] == 34) {
                            lit++
                            b[i]     = 32
                            b[i + 1] = 32
                            i = i + 2
                            continue
                        }
                    }
                    if (b[i] == 34 & i < n) {
                        if (b[i + 1] == 39) {
                            lit--
                            if (lit > 0) {
                                b[i]     = 32
                                b[i + 1] = 32
                            }
                            i = i + 2
                            continue
                        }
                    }
                    b[i] = 32
                    i++
                }
                continue
            }
        }
        if (b[i] == 34) {
            i++
            while (i <= n) {
                if (b[i] == 34) break
                b[i] = 32
                i++
            }
            i++
            continue
        }
        i++
    }
    return(n ? char(b) : "")
}


// _dash_qual_ordered(ifx, inx) -- 1 when the rows the pair selects can
// depend on the order of the observations: an in range, or an if holding
// _n, _N, a subscript [...] or the running sum(), outside its string
// literals.  Any other if reads each row alone and selects the same rows
// in any order, so a by() graph shares the data-order column for it.
real scalar _dash_qual_ordered(string scalar ifx, string scalar inx)
{
    string scalar t

    if (strtrim(inx) != "") return(1)
    t = _dash_qual_blank_lits(ifx)
    if (strpos(t, "[")) return(1)
    if (ustrregexm(t, "(^|[^A-Za-z0-9_])_[nN]($|[^A-Za-z0-9_])")) return(1)
    if (ustrregexm(t, "(^|[^A-Za-z0-9_])sum[ \t]*\(")) return(1)
    return(0)
}


// _dash_qual_by_of(json, total, errmacro) -- the variables of the "by"
// value a registered graph's JSON holds, blank-separated ("" for none);
// total is set to 1 when its sub-options give total (tot at least, as
// twoway's TOTal; a parenthesised sub-option's text is not read), as
// _dash_by_parts reads them.  Each variable must be a Stata name: the
// value comes from a registry that may have been set by hand, and the
// names go on a sort command line (_dash_qual_gen_by).  Two different by
// values, or a by() that names something else, put the reason in the
// caller's local errmacro and return "".
string scalar _dash_qual_by_of(string scalar json, real scalar total,
                               string scalar errmacro)
{
    real rowvector   b
    real scalar      n, i, e, k, depth, cut, j, found
    string scalar    tok, v, byv, vars, opts
    string rowvector w

    total = 0
    b     = ascii(json)
    n     = cols(b)
    byv   = ""
    found = 0
    i     = 1
    while (i <= n) {
        if (b[i] != 34) {
            i++
            continue
        }
        e = i + 1
        while (e <= n) {
            if (b[e] == 34) break
            e = e + (b[e] == 92 ? 2 : 1)
        }
        if (e > n) break
        tok = (e - i > 1 ? substr(json, i + 1, e - i - 1) : "")
        k   = _dash_qual_skipws(b, e + 1)
        if (k > n) break
        if (b[k] != 58 | tok != "by") {
            i = e + 1
            continue
        }
        k = _dash_qual_skipws(b, k + 1)
        if (k > n) break
        if (b[k] != 34) {
            i = k
            continue
        }
        v = _dash_qual_json_text(b, k)
        if (found & v != byv) {
            st_local(errmacro, "it holds two by() values")
            return("")
        }
        byv   = v
        found = 1
        i     = k
    }
    if (strtrim(byv) == "") return("")
    // The variables end at the first comma outside parentheses.
    b     = ascii(byv)
    n     = cols(b)
    depth = 0
    cut   = 0
    for (j = 1; j <= n; j++) {
        if (b[j] == 40) depth++
        else if (b[j] == 41) depth--
        else if (b[j] == 44 & depth == 0) {
            cut = j
            break
        }
    }
    vars = strtrim(cut ? substr(byv, 1, cut - 1) : byv)
    opts = (cut ? substr(byv, cut + 1, .) : "")
    w = tokens(vars)
    if (cols(w) > 20) {
        st_local(errmacro, "its by() names more variables than dash reads (20)")
        return("")
    }
    for (j = 1; j <= cols(w); j++) {
        // A Stata name: letters (Unicode ones too), digits and _, not
        // starting with a digit, at most 32 characters.
        if (!ustrregexm(w[j], "^[\p{L}_][\p{L}\p{N}_]*$") | ustrlen(w[j]) > 32) {
            st_local(errmacro, "its by() does not name variables")
            return("")
        }
    }
    while (ustrregexm(opts, "\([^()]*\)")) opts = ustrregexrf(opts, "\([^()]*\)", " ")
    total = ustrregexm(opts, "(^|[ ,])tot(a|al)?($|[ ,])")
    return(cols(w) ? invtokens(w) : "")
}


// The first byte at or after k that is not a JSON blank; cols(b) + 1 when
// there is none.
real scalar _dash_qual_skipws(real rowvector b, real scalar k)
{
    while (k <= cols(b)) {
        if (b[k] != 32 & b[k] != 9 & b[k] != 10 & b[k] != 13) break
        k++
    }
    return(k)
}


// _dash_qual_rewrite(json, errmacro, name_them) -- a registered graph's
// JSON with each qualifier replaced by the column that holds it.
//
// Every "if_expr":"<a>","in_expr":"<b>" pair -- each plot's and the
// graph's, as _dash_plot writes them -- becomes
// "if_expr":"","in_expr":"","qual_col":"__dashq<k>" (qual_col "" for no
// qualifier).  Keys are found by walking the JSON's strings, so text inside
// a value never matches.  A key dash.ado would not have written there -- an
// "in_expr" alone, a "qual_col" of the registry's own, an "if_expr" without
// its "in_expr" -- or a pair _dash_qual_refusal refuses puts the reason in
// the caller's local errmacro and returns "".  Linear in the JSON: its
// pieces are joined once, at the end.
//
// A by() graph's qualifiers are evaluated as twoway evaluates them:
// bygraph_g.class sorts the data on the by() variables, stably (bysort
// varlist (sortedby obsnum)), and draws every panel from the whole sorted
// data, so `if _n == 1', `in 1/10' or `if mpg > mpg[_n-1]' count rows in
// that order, _n never restarting within a group; by(, total)'s Total
// panel is drawn after `bysort one (sortedby obsnum)', in the data's own
// order (measured 24sep2026 from each panel's serset;
// test_qualifier_in_stata.cscript QS-16..).  A pair whose rows can depend
// on the order (_dash_qual_ordered) takes, in such a graph, the column
// evaluated in the by() order, and under total also "qual_col_total", the
// data-order column its Total panel draws; any other pair keeps the one
// data-order column.  A "qual_col_total" of the registry's own is refused
// as a "qual_col" is.
string scalar _dash_qual_rewrite(string scalar json, string scalar errmacro,
                                 real scalar name_them)
{
    real rowvector   b
    real scalar      n, i, e, k, from, m, cap, total
    string scalar    tok, v1, v2, nm, nt, q, order, eff
    string rowvector part

    q = char(34)
    st_local(errmacro, "")
    total = 0
    order = _dash_qual_by_of(json, total, errmacro)
    if (st_local(errmacro) != "") return("")
    b    = ascii(json)
    n    = cols(b)
    cap  = 16
    part = J(1, cap, "")
    m    = 0
    from = 1
    i    = 1
    while (i <= n) {
        if (b[i] != 34) {
            i++
            continue
        }
        e = i + 1
        while (e <= n) {
            if (b[e] == 34) break
            e = e + (b[e] == 92 ? 2 : 1)
        }
        if (e > n) break
        tok = (e - i > 1 ? substr(json, i + 1, e - i - 1) : "")
        k   = _dash_qual_skipws(b, e + 1)
        if (k > n) break
        if (b[k] != 58 | !anyof(("if_expr", "in_expr", "qual_col", "qual_col_total"), tok)) {
            i = e + 1
            continue
        }
        if (tok != "if_expr") {
            st_local(errmacro, "it holds " + q + tok + q + " where dash writes " +
                q + "if_expr" + q + " and " + q + "in_expr" + q + " together")
            return("")
        }
        // "if_expr" : "<a>" , "in_expr" : "<b>"
        k = _dash_qual_skipws(b, k + 1)
        if (k > n) {
            st_local(errmacro, "its if_expr has no value")
            return("")
        }
        if (b[k] != 34) {
            st_local(errmacro, "its if_expr is not a string")
            return("")
        }
        v1 = _dash_qual_json_text(b, k)
        if (k > n + 1) {
            st_local(errmacro, "its if_expr is not closed")
            return("")
        }
        k = _dash_qual_skipws(b, k)
        if (k > n) {
            st_local(errmacro, "its if_expr has no in_expr beside it")
            return("")
        }
        if (b[k] != 44) {
            st_local(errmacro, "its if_expr has no in_expr beside it")
            return("")
        }
        k = _dash_qual_skipws(b, k + 1)
        if (substr(json, k, 9) != q + "in_expr" + q) {
            st_local(errmacro, "its if_expr has no in_expr beside it")
            return("")
        }
        k = _dash_qual_skipws(b, k + 9)
        if (k > n) {
            st_local(errmacro, "its in_expr has no value")
            return("")
        }
        if (b[k] != 58) {
            st_local(errmacro, "its in_expr has no value")
            return("")
        }
        k = _dash_qual_skipws(b, k + 1)
        if (k > n) {
            st_local(errmacro, "its in_expr has no value")
            return("")
        }
        if (b[k] != 34) {
            st_local(errmacro, "its in_expr is not a string")
            return("")
        }
        v2 = _dash_qual_json_text(b, k)
        if (k > n + 1) {
            st_local(errmacro, "its in_expr is not closed")
            return("")
        }
        eff = (order != "" & _dash_qual_ordered(v1, v2) ? order : "")
        nm  = _dash_qual_take_by(v1, v2, eff, errmacro, name_them)
        if (st_local(errmacro) != "") return("")
        nt  = ""
        if (eff != "" & total) {
            nt = _dash_qual_take_by(v1, v2, "", errmacro, name_them)
            if (st_local(errmacro) != "") return("")
        }
        if (m + 2 > cap) {
            part = part, J(1, cap, "")
            cap  = 2 * cap
        }
        part[++m] = substr(json, from, i - from)
        part[++m] = q + "if_expr" + q + ":" + q + q + "," + q + "in_expr" + q +
                    ":" + q + q + "," + q + "qual_col" + q + ":" + q + nm + q +
                    (nt != "" ? "," + q + "qual_col_total" + q + ":" + q + nt + q : "")
        from = k
        i    = k
    }
    if (m + 1 > cap) part = part, J(1, 1, "")
    part[++m] = substr(json, from, .)
    return(invtokens(part[|1 \ m|], ""))
}


// _dash_qual_export() -- the distinct qualifiers, into the caller's locals:
// _dq_n, and for each k the if and the in of column __dashq<k> in _dq_if_k
// and _dq_in_k, by value, and in _dq_by_k the variables it is evaluated
// sorted on ("" for the data's order; Stata names, _dash_qual_by_of).
void _dash_qual_export()
{
    external string matrix _dash_qual_list
    real scalar k

    st_local("_dq_n", strofreal(rows(_dash_qual_list)))
    for (k = 1; k <= rows(_dash_qual_list); k++) {
        st_local("_dq_if_" + strofreal(k), _dash_qual_list[k, 1])
        st_local("_dq_in_" + strofreal(k), _dash_qual_list[k, 2])
        st_local("_dq_by_" + strofreal(k), _dash_qual_list[k, 3])
        st_local("_dq_fr_" + strofreal(k), _dash_qual_list[k, 4])
    }
}


// _dash_qual_orders() -- the distinct by() orders the table holds, "" left
// out, into the caller's locals: _dq_nord, and _dq_ord_j for each, in the
// order first met.  Linear in the table.
void _dash_qual_orders()
{
    external string matrix _dash_qual_list
    transmorphic scalar    seen
    real scalar            k, j

    seen = asarray_create("string", 1)
    j    = 0
    for (k = 1; k <= rows(_dash_qual_list); k++) {
        if (_dash_qual_list[k, 3] == "") continue
        if (asarray_contains(seen, _dash_qual_list[k, 3])) continue
        asarray(seen, _dash_qual_list[k, 3], 1)
        j++
        st_local("_dq_ord_" + strofreal(j), _dash_qual_list[k, 3])
    }
    st_local("_dq_nord", strofreal(j))
}


// _dash_reserved_prefix(names) -- the prefix this export names its working
// columns with (WP-35 DT-19): __dash when no name of names starts with it,
// else the first __dsh<k>_ (k = 1, 2, ...) none starts with.  names are the
// variable names (and, on the build route, the value-label set names) of
// every frame the export reads, so no column dash makes -- qualifier,
// join-order, time-series, weight, split column, label copy, or a column
// the renderers make -- is a name the data hold, and every variable is
// read as data, as twoway reads it.  The prefix is kept in the external
// _dash_col_prefix for the name writers of this export (_dash_col_pfx).
string scalar _dash_reserved_prefix(string rowvector names)
{
    external string scalar _dash_col_prefix
    string scalar          p
    real scalar            k, j, hit

    p = "__dash"
    for (k = 0; k < 100000; k++) {
        if (k) p = "__dsh" + strofreal(k) + "_"
        hit = 0
        for (j = 1; j <= cols(names); j++) {
            if (substr(names[j], 1, strlen(p)) == p) {
                hit = 1
                break
            }
        }
        if (!hit) break
    }
    _dash_col_prefix = p
    return(p)
}

// _dash_col_pfx() -- the prefix _dash_reserved_prefix chose for this
// export, __dash before it has run.
string scalar _dash_col_pfx()
{
    pointer() scalar p

    p = findexternal("_dash_col_prefix")
    if (p == NULL) return("__dash")
    if (eltype(*p) != "string" | rows(*p) != 1 | cols(*p) != 1) return("__dash")
    if (*p == "") return("__dash")
    return(*p)
}

// _dash_esample_sub(s, nm) -- the expression s with each e(sample) outside
// its string literals read as the variable nm, the copy of e(sample) an
// export makes before it holds the estimates (WP-35 DT-19): twoway reads
// e(sample) as the estimation sample, and a held estimate reads as 0.
string scalar _dash_esample_sub(string scalar s, string scalar nm)
{
    string scalar b, m
    real scalar   p

    b = _dash_qual_blank_lits(s)
    while (regexm(b, "e\( *sample *\)")) {
        m = regexs(0)
        p = strpos(b, m)
        s = substr(s, 1, p - 1) + nm + substr(s, p + strlen(m), .)
        b = substr(b, 1, p - 1) + nm + substr(b, p + strlen(m), .)
    }
    return(s)
}

// _dash_expr_words(s) -- the words of the expression s outside its string
// literals that could name a variable, blank-separated, each once (WP-35
// DT-19: the variables a temporary export frame must carry).
string scalar _dash_expr_words(string scalar s)
{
    string scalar b, w, out
    real scalar   p

    b   = _dash_qual_blank_lits(s)
    out = ""
    while (regexm(b, "[A-Za-z_][A-Za-z0-9_]*")) {
        w = regexs(0)
        p = strpos(b, w)
        if (!anyof(tokens(out), w)) out = out + (out != "" ? " " : "") + w
        b = substr(b, p + strlen(w), .)
    }
    return(out)
}


// ------------------------------------------------------------
// The join-order table (WP-29 P0.1).  Each distinct "sortvars" value a
// dashboard's plots carry -- the names _dash_sort_opt took from
// sort(varlist) on a joining type -- gets one rank column __dashs<k>,
// made in Stata by _dash_sort_gen.  The values are read back from the
// registry's JSON, which a do-file can set by hand, so every token is
// checked to be a name again before any reaches a sort command.
// ------------------------------------------------------------

// _dash_sort_reset() -- empty the table.
void _dash_sort_reset()
{
    external string colvector _dash_sort_list
    external string colvector _dash_sort_frames

    _dash_sort_list   = J(0, 1, "")
    _dash_sort_frames = J(0, 1, "")
}

// _dash_sort_scan(json) -- add every "sortvars" value of json to the
// table, each once, in the order first met (each value read up to the
// next double quote).  Sets the
// caller's local _ds_bad to the first value holding a token that is not a
// Stata name, and leaves it alone otherwise.
void _dash_sort_scan(string scalar json)
{
    external string colvector _dash_sort_list
    external string colvector _dash_sort_frames
    string scalar    needle, tail, val, fk
    string rowvector t
    real scalar      pos, vstart, vend, i, ok, ix

    if (rows(_dash_sort_list) == 0 & cols(_dash_sort_list) == 0) {
        _dash_sort_list = J(0, 1, "")
    }
    // The frames each list is ranked in (WP-33 33-07), " f1 f2 ": one
    // column a list, each frame ranking its own rows, since the spec's
    // sort_cols names one column for a list.
    if (rows(_dash_sort_frames) != rows(_dash_sort_list)) {
        _dash_sort_frames = J(rows(_dash_sort_list), 1, " ")
    }
    fk = " " + _dash_frame_key_now() + " "
    needle = char(34) + "sortvars" + char(34) + ":" + char(34)
    tail   = json
    pos    = strpos(tail, needle)
    while (pos) {
        vstart = pos + strlen(needle)
        vend   = strpos(substr(tail, vstart, .), char(34))
        if (!vend) break
        val = substr(tail, vstart, vend - 1)
        t   = tokens(val)
        ok  = (cols(t) > 0 & val == invtokens(t))
        for (i = 1; i <= cols(t) & ok; i++) ok = st_isname(t[i])
        if (!ok) {
            if (st_local("_ds_bad") == "") st_local("_ds_bad", val)
        }
        else {
            ix = 0
            for (i = 1; i <= rows(_dash_sort_list); i++) {
                if (_dash_sort_list[i] == val) {
                    ix = i
                    break
                }
            }
            if (!ix) {
                _dash_sort_list   = _dash_sort_list \ val
                _dash_sort_frames = _dash_sort_frames \ fk
            }
            else if (!strpos(_dash_sort_frames[ix], fk)) {
                _dash_sort_frames[ix] = _dash_sort_frames[ix] + substr(fk, 2, .)
            }
        }
        tail = substr(tail, vstart + vend, .)
        pos  = strpos(tail, needle)
    }
}

// _dash_sort_export() -- the table into the caller's locals: _ds_n, and
// _ds_v<k>, the names of column __dashs<k>.
void _dash_sort_export()
{
    external string colvector _dash_sort_list
    external string colvector _dash_sort_frames
    real scalar k

    if (rows(_dash_sort_list) == 0 & cols(_dash_sort_list) == 0) {
        _dash_sort_list = J(0, 1, "")
    }
    if (rows(_dash_sort_frames) != rows(_dash_sort_list)) {
        _dash_sort_frames = J(rows(_dash_sort_list), 1, " ")
    }
    st_local("_ds_n", strofreal(rows(_dash_sort_list)))
    for (k = 1; k <= rows(_dash_sort_list); k++) {
        st_local("_ds_v" + strofreal(k), _dash_sort_list[k])
        st_local("_ds_f" + strofreal(k), _dash_sort_frames[k])
    }
}


// ------------------------------------------------------------
// The time-series table (WP-30 P1.7).  twoway draws L.close, D.close and
// L(1/2).close in a plot varlist; -syntax- (varlist(numeric ts)) has
// normalised each to tsunab's form (L.close, LD.close, L2.close) when the
// graph was registered.  Each distinct expression a dashboard's plots
// carry becomes one column __dasht<k>, made in Stata by _dash_tsop_gen
// with tsrevar, as twoway computes it: over every observation, under the
// tsset then in force.  The registry is a set of globals a do-file can
// edit, so every expression is held to the canonical form here, and
// again by _dash_tsop_gen, before tsrevar sees it.
// ------------------------------------------------------------

// _dash_tsop_reset() -- empty the table.
void _dash_tsop_reset()
{
    external string colvector _dash_tsop_list
    external string colvector _dash_tsop_frames

    _dash_tsop_list   = J(0, 1, "")
    _dash_tsop_frames = J(0, 1, "")
}

// _dash_tsop_canon(expr) -- 1 when expr is <ops>.<var>: one or more of the
// operators L, F, D and S, each alone or followed by 1 to 4 digits not led
// by 0 (tsunab writes L1 as L and drops L0), then a dot, then the exact
// name of a variable in memory (no abbreviation).  Read byte by byte:
// regexm's engine follows the caller's version.  A Unicode name passes, as
// twoway takes it; a name holds no blank, quote, semicolon, dollar or
// backtick, so nothing but a variable reaches tsrevar.
real scalar _dash_tsop_canon(string scalar e)
{
    real rowvector b
    real scalar    n, i, d, dot, ix
    string scalar  base

    b   = ascii(e)
    n   = cols(b)
    dot = 0
    for (i = 1; i <= n; i++) {
        if (b[i] == 46) {
            dot = i
            break
        }
    }
    if (dot < 2 | dot == n) return(0)
    i = 1
    while (i < dot) {
        // L F D S
        if (b[i] != 76 & b[i] != 70 & b[i] != 68 & b[i] != 83) return(0)
        i++
        d = 0
        while (i < dot & b[i] >= 48 & b[i] <= 57) {
            if (d == 0 & b[i] == 48) return(0)
            d++
            i++
        }
        if (d > 4) return(0)
    }
    base = substr(e, dot + 1, .)
    if (strlen(base) > 128) return(0)
    ix = _st_varindex(base, 0)
    if (ix >= .) return(0)
    return(st_varname(ix) == base)
}

// _dash_tsop_rewrite(json, errmacro) -- json with each plot-variable value
// holding a dot ("yvar", "xvar", "yvar1", "yvar2", "y1var", "x1var",
// "y2var", "x2var"; and the weight "wexp" when it is a canonical term,
// [aw=L.price], WP-31 A5 -- another weight expression is
// _dash_wexp_rewrite's) replaced by its column
// __dasht<k>, the expression added to the table once.  Keys are found by
// walking the JSON's strings, as _dash_qual_rewrite finds its own.  A
// value that is not the canonical form (_dash_tsop_canon) puts the reason
// in the caller's local errmacro and returns json unchanged.
string scalar _dash_tsop_rewrite(string scalar json, string scalar errmacro)
{
    external string colvector _dash_tsop_list
    external string colvector _dash_tsop_frames
    real rowvector   b
    real scalar      n, i, e, k, v, ve, from, m, cap, ix
    string scalar    tok, val, shown, fk
    string rowvector part, keys

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
    // Each expression is keyed by its frame too (WP-33 33-07).
    if (rows(_dash_tsop_frames) != rows(_dash_tsop_list)) {
        _dash_tsop_frames = J(rows(_dash_tsop_list), 1, "")
    }
    fk = _dash_frame_key_now()
    st_local(errmacro, "")
    keys = ("yvar", "xvar", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var", "wexp")
    b    = ascii(json)
    n    = cols(b)
    cap  = 16
    part = J(1, cap, "")
    m    = 0
    from = 1
    i    = 1
    while (i <= n) {
        if (b[i] != 34) {
            i++
            continue
        }
        e = i + 1
        while (e <= n) {
            if (b[e] == 34) break
            e = e + (b[e] == 92 ? 2 : 1)
        }
        if (e > n) break
        tok = (e - i > 1 ? substr(json, i + 1, e - i - 1) : "")
        k   = _dash_qual_skipws(b, e + 1)
        if (k > n) break
        if (b[k] != 58 | !anyof(keys, tok)) {
            i = e + 1
            continue
        }
        v = _dash_qual_skipws(b, k + 1)
        if (v > n) break
        if (b[v] != 34) {
            i = v
            continue
        }
        ve = v + 1
        while (ve <= n) {
            if (b[ve] == 34) break
            ve = ve + (b[ve] == 92 ? 2 : 1)
        }
        if (ve > n) break
        val = (ve - v > 1 ? substr(json, v + 1, ve - v - 1) : "")
        if (!strpos(val, ".") | (tok == "wexp" & !_dash_tsop_canon(val))) {
            i = ve + 1
            continue
        }
        if (!_dash_tsop_canon(val)) {
            shown = (ustrlen(val) > 80 ? usubstr(val, 1, 77) + "..." : val)
            st_local(errmacro, "registry entry " + shown +
                " holds a variable dash cannot read")
            return(json)
        }
        ix = 0
        for (k = 1; k <= rows(_dash_tsop_list); k++) {
            if (_dash_tsop_list[k] == val & _dash_tsop_frames[k] == fk) {
                ix = k
                break
            }
        }
        if (!ix) {
            if (rows(_dash_tsop_list) >= 9999) {
                st_local(errmacro, "it holds more than 9,999 distinct " +
                    "time-series expressions")
                return(json)
            }
            _dash_tsop_list   = _dash_tsop_list \ val
            _dash_tsop_frames = _dash_tsop_frames \ fk
            ix = rows(_dash_tsop_list)
        }
        if (m + 2 > cap) {
            part = part, J(1, cap, "")
            cap  = 2 * cap
        }
        part[++m] = substr(json, from, v - from)
        part[++m] = char(34) + _dash_col_pfx() + "t" + strofreal(ix) + char(34)
        from = ve + 1
        i    = ve + 1
    }
    if (m + 1 > cap) part = part, J(1, 1, "")
    part[++m] = substr(json, from, .)
    return(invtokens(part[|1 \ m|], ""))
}

// _dash_tsop_export() -- the table into the caller's locals: _dts_n, and
// _dts_e<k>, the expression of column __dasht<k>.
void _dash_tsop_export()
{
    external string colvector _dash_tsop_list
    external string colvector _dash_tsop_frames
    real scalar k

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
    if (rows(_dash_tsop_frames) != rows(_dash_tsop_list)) {
        _dash_tsop_frames = J(rows(_dash_tsop_list), 1, "")
    }
    st_local("_dts_n", strofreal(rows(_dash_tsop_list)))
    for (k = 1; k <= rows(_dash_tsop_list); k++) {
        st_local("_dts_e" + strofreal(k), _dash_tsop_list[k])
        st_local("_dts_f" + strofreal(k), _dash_tsop_frames[k])
    }
}

// _dash_tsop_meta(fmtmacro) -- the spec's "ts_cols" object,
// {"__dasht<k>":{"expr":"L.close","label":"<text>"},...}, and each
// column's display format, its base's, merged into the formats JSON the
// caller's local fmtmacro holds.  <text> is twoway's: the base's label, a
// comma and a space and the operators (Closing price, D), or the
// expression when the base has no label (a label of blanks is a label:
// twoway draws "   , L"); read by value, never cut (an 80-character label
// keeps all 80).  Every value is escaped by
// _dash_json_escape.  The weight columns __dashw<k> of _dash_wexp_rewrite
// follow, {"expr":"price+1","label":"price+1"} (WP-31 A5).
string scalar _dash_tsop_meta(string scalar fmtmacro)
{
    external string colvector _dash_tsop_list
    external string colvector _dash_tsop_frames
    external string colvector _dash_wexp_list
    real scalar   k, dot
    string scalar e, base, lab, out, fmt, nm, q, sp

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
    if (rows(_dash_tsop_frames) != rows(_dash_tsop_list)) {
        _dash_tsop_frames = J(rows(_dash_tsop_list), 1, "")
    }
    q   = char(34)
    out = ""
    fmt = ""
    for (k = 1; k <= rows(_dash_tsop_list); k++) {
        e    = _dash_tsop_list[k]
        dot  = strpos(e, ".")
        base = substr(e, dot + 1, .)
        // On a build of several frames (WP-33 33-07) a base its frame
        // holds in a split column is read from that column: the stack's
        // own base is another frame's.
        if (_dash_tsop_frames[k] != "") {
            sp = _dash_frames_split_of(_dash_tsop_frames[k], base)
            if (sp != "") base = sp
        }
        nm   = _dash_col_pfx() + "t" + strofreal(k)
        lab  = (_st_varindex(base, 0) < . ? st_varlabel(base) : "")
        lab  = (lab != "" ? lab + ", " + substr(e, 1, dot - 1) : e)
        out  = out + (k > 1 ? "," : "") + q + nm + q + ":{" + q + "expr" + q +
               ":" + q + _dash_json_escape(e) + q + "," + q + "label" + q + ":" +
               q + _dash_json_escape(lab) + q + "}"
        if (_st_varindex(base, 0) < .) {
            fmt = fmt + (fmt != "" ? "," : "") + q + nm + q + ":" + q +
                  _dash_json_escape(st_varformat(base)) + q
        }
    }
    // The weight columns (WP-31 A5): the expression as typed, which is
    // also the text a note shows for the column.
    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
    for (k = 1; k <= rows(_dash_wexp_list); k++) {
        e   = _dash_wexp_list[k]
        nm  = _dash_col_pfx() + "w" + strofreal(k)
        out = out + (out != "" ? "," : "") + q + nm + q + ":{" + q + "expr" +
              q + ":" + q + _dash_json_escape(e) + q + "," + q + "label" + q +
              ":" + q + _dash_json_escape(e) + q + "}"
    }
    if (fmt != "") {
        e = strtrim(st_local(fmtmacro))
        if (e == "" | e == "{}") st_local(fmtmacro, "{" + fmt + "}")
        else st_local(fmtmacro, substr(e, 1, strlen(e) - 1) + "," + fmt + "}")
    }
    return("{" + out + "}")
}


// ------------------------------------------------------------
// The weight-expression table (WP-31 A5).  twoway evaluates a weight
// expression itself ([aw=price+1]); dash.ado checked it at registration
// with Stata's own generate, and each distinct expression a dashboard's
// layers carry becomes one column __dashw<k>, made in Stata by
// _dash_wexp_gen at export, as the time-series columns are.  A canonical
// time-series term ([aw=L.price]) is _dash_tsop_rewrite's, and a bare
// variable name is read as the column it names.  The registry is a set
// of globals a do-file can edit, so every expression is held to
// _dash_wexp_ok here and again by _dash_wexp_gen before generate sees it.
// ------------------------------------------------------------

// _dash_wexp_ok(e) -- 1 when a weight expression may reach generate: not
// empty, at most 512 bytes, and holding no backtick, dollar sign, double
// quote, semicolon, tab or line break (WP-31 A5, D-07.a).  Read byte by
// byte: no regex (regexm follows the caller's version).
real scalar _dash_wexp_ok(string scalar e)
{
    real rowvector b
    real scalar    i

    if (strlen(e) == 0 | strlen(e) > 512) return(0)
    b = ascii(e)
    for (i = 1; i <= cols(b); i++) {
        if (b[i] == 96 | b[i] == 36 | b[i] == 34 | b[i] == 59 |
            b[i] == 9 | b[i] == 10 | b[i] == 13) return(0)
    }
    return(1)
}

// _dash_wexp_reset() -- empty the table.
void _dash_wexp_reset()
{
    external string colvector _dash_wexp_list
    external string colvector _dash_wexp_frames

    _dash_wexp_list   = J(0, 1, "")
    _dash_wexp_frames = J(0, 1, "")
}

// _dash_wexp_rewrite(json, errmacro) -- json with each "wexp" value that is
// neither the exact name of a variable in memory nor a canonical
// time-series term (_dash_tsop_canon) replaced by its column __dashw<k>,
// the expression added to the table once.  Keys are found by walking the
// JSON's strings, as _dash_tsop_rewrite finds its own.  A value
// _dash_wexp_ok refuses, or holding a JSON escape, puts the reason in the
// caller's local errmacro and returns json unchanged.
string scalar _dash_wexp_rewrite(string scalar json, string scalar errmacro)
{
    external string colvector _dash_wexp_list
    external string colvector _dash_wexp_frames
    real rowvector   b
    real scalar      n, i, e, k, v, ve, from, m, cap, ix
    string scalar    tok, val, shown, fk
    string rowvector part

    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
    // Each expression is keyed by its frame too (WP-33 33-07).
    if (rows(_dash_wexp_frames) != rows(_dash_wexp_list)) {
        _dash_wexp_frames = J(rows(_dash_wexp_list), 1, "")
    }
    fk = _dash_frame_key_now()
    st_local(errmacro, "")
    b    = ascii(json)
    n    = cols(b)
    cap  = 16
    part = J(1, cap, "")
    m    = 0
    from = 1
    i    = 1
    while (i <= n) {
        if (b[i] != 34) {
            i++
            continue
        }
        e = i + 1
        while (e <= n) {
            if (b[e] == 34) break
            e = e + (b[e] == 92 ? 2 : 1)
        }
        if (e > n) break
        tok = (e - i > 1 ? substr(json, i + 1, e - i - 1) : "")
        k   = _dash_qual_skipws(b, e + 1)
        if (k > n) break
        if (b[k] != 58 | tok != "wexp") {
            i = e + 1
            continue
        }
        v = _dash_qual_skipws(b, k + 1)
        if (v > n) break
        if (b[v] != 34) {
            i = v
            continue
        }
        ve = v + 1
        while (ve <= n) {
            if (b[ve] == 34) break
            ve = ve + (b[ve] == 92 ? 2 : 1)
        }
        if (ve > n) break
        val = (ve - v > 1 ? substr(json, v + 1, ve - v - 1) : "")
        if (val == "" | _dash_tsop_canon(val)) {
            i = ve + 1
            continue
        }
        if (strlen(val) <= 32 & _st_varindex(val, 0) < .) {
            if (st_varname(_st_varindex(val, 0)) == val) {
                i = ve + 1
                continue
            }
        }
        if (!_dash_wexp_ok(val) | strpos(val, char(92))) {
            shown = (ustrlen(val) > 80 ? usubstr(val, 1, 77) + "..." : val)
            st_local(errmacro, "registry entry [" + shown +
                "] holds a weight dash cannot evaluate")
            return(json)
        }
        ix = 0
        for (k = 1; k <= rows(_dash_wexp_list); k++) {
            if (_dash_wexp_list[k] == val & _dash_wexp_frames[k] == fk) {
                ix = k
                break
            }
        }
        if (!ix) {
            if (rows(_dash_wexp_list) >= 9999) {
                st_local(errmacro, "it holds more than 9,999 distinct " +
                    "weight expressions")
                return(json)
            }
            _dash_wexp_list   = _dash_wexp_list \ val
            _dash_wexp_frames = _dash_wexp_frames \ fk
            ix = rows(_dash_wexp_list)
        }
        if (m + 2 > cap) {
            part = part, J(1, cap, "")
            cap  = 2 * cap
        }
        part[++m] = substr(json, from, v - from)
        part[++m] = char(34) + _dash_col_pfx() + "w" + strofreal(ix) + char(34)
        from = ve + 1
        i    = ve + 1
    }
    if (m + 1 > cap) part = part, J(1, 1, "")
    part[++m] = substr(json, from, .)
    return(invtokens(part[|1 \ m|], ""))
}

// _dash_wexp_export() -- the table into the caller's locals: _dwx_n, and
// _dwx_e<k>, the expression of column __dashw<k>.
void _dash_wexp_export()
{
    external string colvector _dash_wexp_list
    external string colvector _dash_wexp_frames
    real scalar k

    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
    if (rows(_dash_wexp_frames) != rows(_dash_wexp_list)) {
        _dash_wexp_frames = J(rows(_dash_wexp_list), 1, "")
    }
    st_local("_dwx_n", strofreal(rows(_dash_wexp_list)))
    for (k = 1; k <= rows(_dash_wexp_list); k++) {
        st_local("_dwx_e" + strofreal(k), _dash_wexp_list[k])
        st_local("_dwx_f" + strofreal(k), _dash_wexp_frames[k])
    }
}


// ------------------------------------------------------------
// Graphs from several frames (WP-33 33-07).  A graph registered under
// Stata's frame prefix (frame f: dash ..., name(g)) is drawn from frame f.
// On such a build every qualifier, time-series and weight column is keyed
// by its frame (_dash_frame_key_now); each frame keeps the variables its
// graphs use; and a variable two frames hold with another storage kind,
// display format, value label or variable label is kept by the later
// frame under a split column __dashm<k> (DECISIONS A-23), a value-label
// set of one name and other contents under __dashl<j>.  The externals
// live for one build: _dash_frames_reset() empties them.
// ------------------------------------------------------------

// _dash_frame_set(f) -- the frame the table entries made next belong to;
// "" on a build of one frame.
void _dash_frame_set(string scalar f)
{
    external string scalar _dash_frame_key

    _dash_frame_key = f
}

// _dash_frame_set_all(on) -- 1: every plot's qualifier pair, the empty
// one included, takes a column (a build of several frames).
void _dash_frame_set_all(real scalar on)
{
    external real scalar _dash_frame_all

    _dash_frame_all = (on == 1)
}

// _dash_frame_key_now() -- the frame key, "" when none was set.
string scalar _dash_frame_key_now()
{
    pointer() scalar p

    p = findexternal("_dash_frame_key")
    if (p == NULL) return("")
    if (eltype(*p) != "string" | rows(*p) != 1 | cols(*p) != 1) return("")
    return(*p)
}

// _dash_frame_all_now() -- 1 when every pair takes a column.
real scalar _dash_frame_all_now()
{
    pointer() scalar p

    p = findexternal("_dash_frame_all")
    if (p == NULL) return(0)
    if (eltype(*p) != "real" | rows(*p) != 1 | cols(*p) != 1) return(0)
    return(*p == 1)
}

// _dash_frames_reset() -- empty the build's frame records.
void _dash_frames_reset()
{
    external transmorphic scalar _dash_frames_owner, _dash_frames_split,
                                 _dash_frames_splitrec, _dash_frames_keep,
                                 _dash_frames_gkeep, _dash_frames_lseen,
                                 _dash_frames_lsets
    external string matrix       _dash_frames_gorder
    external real scalar         _dash_frames_nsplit, _dash_frames_nlset

    _dash_frames_owner    = asarray_create("string", 1)
    _dash_frames_split    = asarray_create("string", 1)
    _dash_frames_splitrec = asarray_create("string", 1)
    _dash_frames_keep     = asarray_create("string", 1)
    _dash_frames_gkeep    = asarray_create("string", 1)
    _dash_frames_lseen    = asarray_create("string", 1)
    _dash_frames_lsets    = asarray_create("string", 1)
    _dash_frames_gorder   = J(0, 2, "")
    _dash_frames_nsplit   = 0
    _dash_frames_nlset    = 0
}

// _dash_frames_keep_add(f, g, vars) -- the names vars into frame f's keep
// list, each once in the order first met; with g not "", also into graph
// g's own list (the variables frame_cols may map for g).
void _dash_frames_keep_add(string scalar f, string scalar g,
                           string scalar vars)
{
    external transmorphic scalar _dash_frames_keep, _dash_frames_gkeep
    external string matrix       _dash_frames_gorder
    string rowvector v
    string scalar    cur
    real scalar      i

    v   = tokens(vars)
    cur = (asarray_contains(_dash_frames_keep, f) ?
           asarray(_dash_frames_keep, f) : "")
    for (i = 1; i <= cols(v); i++) {
        if (!anyof(tokens(cur), v[i])) cur = cur + " " + v[i]
    }
    asarray(_dash_frames_keep, f, strtrim(cur))
    if (g == "") return
    if (!asarray_contains(_dash_frames_gkeep, g)) {
        _dash_frames_gorder = _dash_frames_gorder \ (g, f)
        cur = ""
    }
    else cur = asarray(_dash_frames_gkeep, g)
    for (i = 1; i <= cols(v); i++) {
        if (!anyof(tokens(cur), v[i])) cur = cur + " " + v[i]
    }
    asarray(_dash_frames_gkeep, g, strtrim(cur))
}

// _dash_frames_keep_of(f) -- frame f's keep list.
string scalar _dash_frames_keep_of(string scalar f)
{
    external transmorphic scalar _dash_frames_keep

    if (!asarray_contains(_dash_frames_keep, f)) return("")
    return(asarray(_dash_frames_keep, f))
}

// _dash_vl_hash(lab) -- the contents of value label lab in the data in
// memory, its values and texts joined; "" when it is not defined.
string scalar _dash_vl_hash(string scalar lab)
{
    real colvector   vals
    string colvector txt
    string scalar    out
    real scalar      i

    if (lab == "") return("")
    if (!st_vlexists(lab)) return("")
    st_vlload(lab, vals, txt)
    out = ""
    for (i = 1; i <= rows(vals); i++) {
        out = out + strofreal(vals[i], "%21.0g") + char(2) + txt[i] + char(3)
    }
    return(out)
}

// _dash_var_meta(v) -- variable v's record in the data in memory:
// kind, format, value-label name, value-label contents and variable label,
// separated by char(1).
string scalar _dash_var_meta(string scalar v)
{
    string scalar sep, vl

    sep = char(1)
    vl  = st_varvaluelabel(v)
    return((st_isstrvar(v) ? "string" : "numeric") + sep + st_varformat(v) +
           sep + vl + sep + _dash_vl_hash(vl) + sep + st_varlabel(v))
}

// _dash_frames_clash(meta1, meta2, v) -- "" when two records of v agree,
// else the first difference: storage kind, display format, value label
// (its contents; the set's name alone is not a difference) or variable
// label.
string scalar _dash_frames_clash(string scalar meta1, string scalar meta2,
                                 string scalar v)
{
    string rowvector a, b, what
    real scalar      i

    a    = _dash_frames_fields(meta1)
    b    = _dash_frames_fields(meta2)
    what = ("storage kind", "display format", "", "value label",
            "variable label")
    for (i = 1; i <= 5; i++) {
        if (i == 3) continue
        if (a[i] != b[i]) return(what[i])
    }
    return("")
}

// _dash_frames_fields(meta) -- a record's five fields.
string rowvector _dash_frames_fields(string scalar meta)
{
    string rowvector out
    string scalar    rest
    real scalar      i, p

    out  = J(1, 5, "")
    rest = meta
    for (i = 1; i <= 4; i++) {
        p = strpos(rest, char(1))
        if (!p) {
            out[i] = rest
            rest   = ""
            continue
        }
        out[i] = substr(rest, 1, p - 1)
        rest   = substr(rest, p + 1, .)
    }
    out[5] = rest
    return(out)
}

// _dash_frames_take(f, v) -- run with frame f's data in memory: "" when
// f keeps v under its own name (the first frame to keep v, or one whose
// record matches that frame's), else the split column __dashm<k> f keeps
// it under, an earlier one reused for an identical record.
string scalar _dash_frames_take(string scalar f, string scalar v)
{
    external transmorphic scalar _dash_frames_owner, _dash_frames_split,
                                 _dash_frames_splitrec
    external real scalar         _dash_frames_nsplit
    string scalar rec, col, rk

    rec = _dash_var_meta(v)
    if (!asarray_contains(_dash_frames_owner, v)) {
        asarray(_dash_frames_owner, v, rec)
        return("")
    }
    if (_dash_frames_clash(asarray(_dash_frames_owner, v), rec, v) == "") {
        return("")
    }
    rk = v + char(0) + rec
    if (asarray_contains(_dash_frames_splitrec, rk)) {
        col = asarray(_dash_frames_splitrec, rk)
    }
    else {
        _dash_frames_nsplit = _dash_frames_nsplit + 1
        col = _dash_col_pfx() + "m" + strofreal(_dash_frames_nsplit)
        asarray(_dash_frames_splitrec, rk, col)
    }
    asarray(_dash_frames_split, f + char(0) + v, col)
    return(col)
}

// _dash_frames_lset(lab) -- run with a frame's data in memory: "" when
// value label lab may travel under its own name (the first frame to use
// it, or one whose contents match), else the set __dashl<j> its contents
// travel under, one per distinct name and contents.
string scalar _dash_frames_lset(string scalar lab)
{
    external transmorphic scalar _dash_frames_lseen, _dash_frames_lsets
    external real scalar         _dash_frames_nlset
    string scalar h, k, nm

    h = _dash_vl_hash(lab)
    if (!asarray_contains(_dash_frames_lseen, lab)) {
        asarray(_dash_frames_lseen, lab, h)
        return("")
    }
    if (asarray(_dash_frames_lseen, lab) == h) return("")
    k = lab + char(0) + h
    if (asarray_contains(_dash_frames_lsets, k)) return(asarray(_dash_frames_lsets, k))
    _dash_frames_nlset = _dash_frames_nlset + 1
    nm = _dash_col_pfx() + "l" + strofreal(_dash_frames_nlset)
    asarray(_dash_frames_lsets, k, nm)
    return(nm)
}

// _dash_frames_split_of(f, v) -- the split column frame f keeps v under,
// "" for none.
string scalar _dash_frames_split_of(string scalar f, string scalar v)
{
    pointer() scalar p

    p = findexternal("_dash_frames_split")
    if (p == NULL) return("")
    if (eltype(*p) == "real" | eltype(*p) == "string") return("")
    if (!asarray_contains(*p, f + char(0) + v)) return("")
    return(asarray(*p, f + char(0) + v))
}

// _dash_frames_cols_json() -- the spec's build_options.frame_cols object:
// for each graph, in registry order, each of its variables its frame
// keeps in a split column, {"<g>":{"<v>":{"col":"__dashm<k>","frame":
// "<f>"}}}; "{}" when nothing was split.
string scalar _dash_frames_cols_json()
{
    external transmorphic scalar _dash_frames_gkeep
    external string matrix       _dash_frames_gorder
    string rowvector v
    string scalar    out, one, q, col
    real scalar      i, j

    q   = char(34)
    out = ""
    for (i = 1; i <= rows(_dash_frames_gorder); i++) {
        v   = tokens(asarray(_dash_frames_gkeep, _dash_frames_gorder[i, 1]))
        one = ""
        for (j = 1; j <= cols(v); j++) {
            col = _dash_frames_split_of(_dash_frames_gorder[i, 2], v[j])
            if (col == "") continue
            one = one + (one != "" ? "," : "") + q + _dash_json_escape(v[j]) +
                  q + ":{" + q + "col" + q + ":" + q + col + q + "," + q +
                  "frame" + q + ":" + q +
                  _dash_json_escape(_dash_frames_gorder[i, 2]) + q + "}"
        }
        if (one == "") continue
        out = out + (out != "" ? "," : "") + q +
              _dash_json_escape(_dash_frames_gorder[i, 1]) + q + ":{" + one + "}"
    }
    return("{" + out + "}")
}

// _dash_filter_exclude_add(filter, k, names) -- filter with the graphs
// names added to group k's exclude(): the group gains exclude() holding
// its own exclude() names and names, written last, where the renderer
// reads the last exclude() of a group; the groups read as
// _dash_filter_refusal reads them.
string scalar _dash_filter_exclude_add(string scalar filter, real scalar k,
                                       string scalar names)
{
    string rowvector groups, had, add
    string scalar    out, grp, all
    real scalar      g, i

    groups = _dash_filter_split(filter, 1)
    out    = ""
    for (g = 1; g <= cols(groups); g++) {
        grp = groups[g]
        add = tokens(names)
        if (g == k & cols(add) > 0) {
            had = _dash_filter_excludes(grp)
            all = invtokens(had)
            for (i = 1; i <= cols(add); i++) {
                if (!anyof(had, add[i])) all = all + (all != "" ? " " : "") + add[i]
            }
            grp = _dash_blank_trim(grp)
            grp = grp + (_dash_first_comma_pos(grp) ? " " : ", ") +
                  "exclude(" + all + ")"
        }
        out = out + (g > 1 ? " || " : "") + grp
    }
    return(out)
}


// ============================================================
// 7.  FILTER EXTRACTION
//     _dash_extract_filters(filter_out, cmd_out)
//
// Scans Stata's `0' local for ALL occurrences of filter(...)
// (case-insensitive, supports abbreviated forms filt/filte/filter).
// Returns:
//   filter_out — specs joined with " || "
//                e.g. "foreign, type(dropdown) || weight, type(range)"
//   cmd_out    — `0' with every filter() group removed so that
//                the caller can pass it back to -syntax- without
//                triggering the "option may not be repeated" error.
//
// Called from _dash_build, _dash_serve_spec and _dash_prepare_spec,
// before -syntax- reads the command.
// ============================================================
void _dash_extract_filters(string scalar filter_out,
                            string scalar cmd_out) {
    string scalar raw, lraw, result, remaining, ch, inner
    real scalar   i, n, depth, jj, k, klen, matched, before_ok
    real scalar   in_dq, in_cq, nxt, k_dq, k_cq, out_depth

    raw       = st_local("0")   // raw command string
    lraw      = strlower(raw)
    n         = strlen(raw)
    result    = ""
    remaining = ""
    i         = 1
    in_dq     = 0
    in_cq     = 0
    out_depth = 0

    while (i <= n) {
        // Quoted text is the user's, not syntax.  This scan had no quote
        // handling at all, so `filter(' written inside a title was
        // harvested as a real filter widget AND cut out of the title:
        //     dash build, title("Q1 filter(foreign) report")
        // rendered as "Q1 report" with rc 0 and no warning.  Matching is
        // done against the lower-cased copy, so it fired on `FILTER(' too.
        nxt = _dash_quote_step(raw, n, i, in_dq, in_cq)
        if (nxt) {
            remaining = remaining + substr(raw, i, nxt - i)
            i = nxt
            continue
        }

        // Attempt to match a filter keyword at position i.
        // Accepted abbreviated forms: filt(4), filte(5), filter(6).
        //
        // Only at paren depth 0: filter() is a top-level option of
        // `dash build' and `dash serve', never a sub-option of another.
        // Without this the scan reached inside any option that happened to
        // contain the word -- measured, `tabs(a, filter(x))' harvested `x'
        // as a real filter and left the user with `tabs(a, )'.
        matched = 0
        klen    = 0

        if (out_depth > 0) {
            // fall through to the copy-one-character path below
        }
        else if (i + 5 <= n & substr(lraw, i, 6) == "filter") {
            matched = 1; klen = 6
        }
        else if (i + 4 <= n & substr(lraw, i, 5) == "filte") {
            matched = 1; klen = 5
        }
        else if (i + 3 <= n & substr(lraw, i, 4) == "filt") {
            matched = 1; klen = 4
        }

        if (matched) {
            // Word-boundary check: preceding char must be space, comma, tab, or start.
            // In standard Stata syntax, options may be written as ",filter(...)" (no space
            // after the comma), so comma is a valid word boundary here.
            real scalar _prev_ch_ok
            string scalar _prev_ch
            _prev_ch = (i > 1 ? substr(raw, i-1, 1) : "")
            _prev_ch_ok = (i == 1 | _prev_ch == " " | _prev_ch == "," | _prev_ch == char(9))
            before_ok = _prev_ch_ok
            if (!before_ok) {
                remaining = remaining + substr(raw, i, 1)
                i++
                continue
            }

            // Skip optional whitespace between keyword and "("
            jj = i + klen
            while (jj <= n & substr(raw, jj, 1) == " ") jj++

            // Must be followed by "(" to be a filter option.
            if (jj <= n & substr(raw, jj, 1) == "(") {
                depth = 1
                k     = jj + 1
                k_dq  = 0
                k_cq  = 0
                while (k <= n & depth > 0) {
                    // Quote-aware here too, so a filter whose own argument
                    // carries an unbalanced paren in a quoted label --
                    //     filter(foreign, label("a (b"))
                    // -- does not run the matcher off the end of the string.
                    nxt = _dash_quote_step(raw, n, k, k_dq, k_cq)
                    if (nxt) {
                        k = nxt
                        continue
                    }
                    ch = substr(raw, k, 1)
                    if      (ch == "(") depth++
                    else if (ch == ")") depth--
                    k++
                }
                // k now points one past the closing ")".
                if (depth == 0) {
                    inner = strtrim(substr(raw, jj+1, k-2-jj))
                    if (result != "") result = result + " || "
                    result = result + inner
                    // Skip trailing spaces so remaining stays clean.
                    i = k
                    while (i <= n & substr(raw, i, 1) == " ") i++
                    continue
                }
            }
        }

        // Track the depth of the option this character sits in, so the
        // keyword test above can require top level.
        ch = substr(raw, i, 1)
        if      (ch == "(") out_depth++
        else if (ch == ")" & out_depth > 0) out_depth--

        remaining = remaining + ch
        i++
    }

    st_local(filter_out, result)
    st_local(cmd_out,    strtrim(remaining))
}


// ============================================================
// 7a. LINK GROUPS (WP-31 H2l)
//     _dash_extract_links(link_out, cmd_out)
//
// link() may be given more than once: each copy is a link group, with a
// source of its own (link(g1 g2) link(g3 g4)).  -syntax- takes one copy
// of an option, so with two or more copies this takes every top-level
// link(...) out of `0' -- quote-aware and at paren depth 0, as
// _dash_extract_filters reads filter() -- and joins their texts with
// " || ", the renderer's group separator (_dash_link_groups).  With one
// copy or none it changes nothing (both locals ""), so a single link()
// reaches -syntax- exactly as before.
// ============================================================
void _dash_extract_links(string scalar link_out, string scalar cmd_out) {
    string scalar raw, lraw, result, remaining, ch, pc
    real scalar   i, n, jj, k, depth, nxt, in_dq, in_cq, k_dq, k_cq
    real scalar   out_depth, copies

    raw       = st_local("0")
    lraw      = strlower(raw)
    n         = strlen(raw)
    result    = ""
    remaining = ""
    copies    = 0
    i         = 1
    in_dq     = 0
    in_cq     = 0
    out_depth = 0
    while (i <= n) {
        nxt = _dash_quote_step(raw, n, i, in_dq, in_cq)
        if (nxt) {
            remaining = remaining + substr(raw, i, nxt - i)
            i = nxt
            continue
        }
        pc = (i > 1 ? substr(raw, i - 1, 1) : "")
        if (out_depth == 0 & i + 3 <= n & substr(lraw, i, 4) == "link" &
            (i == 1 | pc == " " | pc == "," | pc == char(9))) {
            jj = i + 4
            while (jj <= n & substr(raw, jj, 1) == " ") jj++
            if (jj <= n & substr(raw, jj, 1) == "(") {
                depth = 1
                k     = jj + 1
                k_dq  = 0
                k_cq  = 0
                while (k <= n & depth > 0) {
                    nxt = _dash_quote_step(raw, n, k, k_dq, k_cq)
                    if (nxt) {
                        k = nxt
                        continue
                    }
                    ch = substr(raw, k, 1)
                    if      (ch == "(") depth++
                    else if (ch == ")") depth--
                    k++
                }
                if (depth == 0) {
                    if (copies) result = result + " || "
                    result = result + strtrim(substr(raw, jj + 1, k - 2 - jj))
                    copies++
                    i = k
                    while (i <= n & substr(raw, i, 1) == " ") i++
                    continue
                }
            }
        }
        ch = substr(raw, i, 1)
        if      (ch == "(") out_depth++
        else if (ch == ")" & out_depth > 0) out_depth--
        remaining = remaining + ch
        i++
    }
    if (copies < 2) {
        st_local(link_out, "")
        st_local(cmd_out,  "")
        return
    }
    st_local(link_out, result)
    st_local(cmd_out,  strtrim(remaining))
}


// ============================================================
// 7b. FILTER GROUPS
//     _dash_filter_split(s, groups)
//     _dash_filter_items(group)
//     _dash_filter_refusal(filter, registry, vars_out)
//     _dash_filter_setvars(filter, names)
//
// _dash_extract_filters joins the filter() groups with " || ", and a
// group's own text may hold "||", ";" or the word "exclude(" -- in its
// label().  dash.ado split the joined string at every "||" and ";" and
// took every "exclude(" for the sub-option, wherever it stood; measured at
// 4ede074, label("A;B") and label("A||B") stopped dash build with "too few
// quotes" r(132), label(A;B) was refused as naming a variable 'B)', and
// label("exclude(nosuch) me") as an exclude() of a graph named nosuch.  A
// group ends only at a "||" or ";" outside quotes and parentheses, and
// exclude() is read only where a sub-option stands.  dash_render.py's
// _dash_filter_split is the same rule (test_help_claims_3.cscript
// checks that the two agree).
// ============================================================

// 1 when ch is one of the six ASCII blanks: space, tab, LF, VT, FF, CR.
real scalar _dash_is_blank(string scalar ch) {
    real scalar b

    if (strlen(ch) != 1) return(0)
    b = ascii(ch)
    return(b == 32 | (b >= 9 & b <= 13))
}

// s without the ASCII blanks at either end.
string scalar _dash_blank_trim(string scalar s) {
    real scalar i, j

    i = 1
    j = strlen(s)
    while (i <= j & _dash_is_blank(substr(s, i, 1))) i++
    while (j >= i & _dash_is_blank(substr(s, j, 1))) j--
    return(substr(s, i, j - i + 1))
}

// The words of s between runs of ASCII blanks, quotes and all -- as
// dash_render.py reads link() and exclude(), with str.split().  Mata's
// tokens() binds a quoted run into one word and drops its quotes, so a name
// written "g1" was g1 to dash, which accepted it, and "g1" to the renderer:
// for exclude("g1") it built no widget, rc 0 (measured 24sep2026;
// test_json_escaping.cscript JSE-56), and for link() it looks for a graph
// named "g1", quotes and all.  Every word dash accepts is a name,
// which holds no blank of any kind, so the renderer's wider set of blanks
// cannot split it further.  Two passes, so a long text costs linear time.
string rowvector _dash_blank_words(string scalar s) {
    string rowvector out
    real scalar      n, i, k, st, inw

    n   = strlen(s)
    k   = 0
    inw = 0
    for (i = 1; i <= n; i++) {
        if (_dash_is_blank(substr(s, i, 1))) inw = 0
        else if (!inw) {
            inw = 1
            k++
        }
    }
    out = J(1, k, "")
    k   = 0
    st  = 0
    for (i = 1; i <= n + 1; i++) {
        if (i > n | _dash_is_blank(substr(s, i, 1))) {
            if (st) {
                k++
                out[k] = substr(s, st, i - st)
                st = 0
            }
        }
        else if (!st) st = i
    }
    return(out)
}

// The pieces of s between its separators, each trimmed, empty ones left
// out.  A separator counts only outside quotes -- "..." and `"..."', read
// by _dash_quote_step -- and outside parentheses.  With groups != 0 the
// separators are "||" and ";", which part the filter() groups; otherwise
// the ASCII blanks and ",", which part one group's sub-options.
string rowvector _dash_filter_split(string scalar s, real scalar groups) {
    string rowvector out
    string scalar    ch, piece
    real scalar      n, i, st, depth, in_dq, in_cq, nxt, w

    out   = J(1, 0, "")
    n     = strlen(s)
    depth = 0
    in_dq = 0
    in_cq = 0
    st    = 1
    i     = 1
    while (i <= n) {
        nxt = _dash_quote_step(s, n, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }
        ch = substr(s, i, 1)
        w  = 0
        if (ch == "(") depth++
        else if (ch == ")") {
            if (depth > 0) depth--
        }
        else if (depth == 0) {
            if (groups) {
                if (ch == ";") w = 1
                else if (ch == "|" & substr(s, i + 1, 1) == "|") w = 2
            }
            else if (ch == "," | _dash_is_blank(ch)) w = 1
        }
        if (w) {
            piece = _dash_blank_trim(substr(s, st, i - st))
            if (piece != "") out = out, piece
            i  = i + w
            st = i
            continue
        }
        i++
    }
    piece = _dash_blank_trim(substr(s, st, .))
    if (piece != "") out = out, piece
    return(out)
}

// A group's variable, then its sub-options.  The variable is the text up
// to the group's first comma outside quotes and parentheses, trimmed --
// its first word when it has no such comma -- as dash.ado has always read
// it, so a name with a blank in it is refused whole rather than cut.
string rowvector _dash_filter_items(string scalar group) {
    string rowvector words
    real scalar      c

    c = _dash_first_comma_pos(group)
    if (c > 0) {
        return(_dash_blank_trim(substr(group, 1, c - 1)),
               _dash_filter_split(substr(group, c + 1, .), 0))
    }
    words = _dash_filter_split(group, 0)
    if (cols(words) == 0) return("")
    return(words)
}

// "" when every exclude() name of every group is in registry and every
// group names a variable that is a Stata name (G5, WP-28: Unicode letters
// included, _dash_is_varname), and vars_out is then set to those variables,
// blank-separated; otherwise the refusal, without
// the command's name -- the exclude() names first, as dash build has always
// checked them first.  A sub-option is exclude() when its name, in any case,
// is exclude and a parenthesis follows (dash_render.py's _dash_subopt_name).
string scalar _dash_filter_refusal(string scalar filter,
                                   string scalar registry,
                                   string scalar vars_out) {
    string rowvector groups, items, reg, names, vars
    string scalar    v, nm, arg, ftype, fdir
    real scalar      g, k, p, hasdir

    st_local(vars_out, "")
    groups = _dash_filter_split(filter, 1)
    reg    = tokens(registry)
    for (g = 1; g <= cols(groups); g++) {
        // Split as the renderer splits it, quotes kept: tokens() took
        // exclude("g1") for g1, and the renderer, reading "g1", built no
        // widget, rc 0 (measured 24sep2026; JSE-56).  _dash_filter_excludes
        // (WP-28 G3) is the one reader of a group's exclude() names, so
        // every reading of them is the same.
        names = _dash_filter_excludes(groups[g])
        for (k = 1; k <= cols(names); k++) {
            if (!anyof(reg, names[k])) {
                return("filter exclude() name '" + names[k] +
                       "' not found in registry.")
            }
        }
    }
    vars = J(1, 0, "")
    for (g = 1; g <= cols(groups); g++) {
        items = _dash_filter_items(groups[g])
        v     = items[1]
        if (!_dash_is_varname(v)) {
            // Every character a name cannot hold, and at most 40 of them:
            // this text is by definition not a variable name, and is shown.
            // G5 (WP-28): a Unicode letter is not replaced, only a
            // character no Stata name can hold at all.
            return("filter() names '" +
                   ustrregexra(usubstr(v, 1, 40), "[^\p{L}\p{N}_.\-]", "?") +
                   "', which is not a valid Stata variable name.")
        }
        // direction(ltr|rtl), on a slider or range only (WP-31 H2f): a
        // sub-option is read as the renderer reads it, its name in any
        // case, its word trimmed and lower-cased.
        ftype  = "dropdown"
        fdir   = ""
        hasdir = 0
        for (k = 2; k <= cols(items); k++) {
            p = strpos(items[k], "(")
            if (!p) continue
            nm  = strlower(_dash_blank_trim(substr(items[k], 1, p - 1)))
            arg = substr(items[k], p + 1, .)
            if (substr(arg, strlen(arg), 1) == ")") {
                arg = substr(arg, 1, strlen(arg) - 1)
            }
            arg = strlower(_dash_blank_trim(arg))
            if (nm == "type") ftype = arg
            else if (nm == "direction") {
                fdir   = arg
                hasdir = 1
            }
        }
        if (hasdir) {
            if (fdir != "ltr" & fdir != "rtl") {
                return("filter(): direction() takes ltr or rtl; got '" +
                       ustrregexra(usubstr(fdir, 1, 40), "[^\p{L}\p{N}_.\-]",
                                   "?") + "'")
            }
            if (ftype != "slider" & ftype != "range") {
                return("filter(): direction() applies to type(slider) and type(range)")
            }
        }
        vars = vars, v
    }
    st_local(vars_out, invtokens(vars))
    return("")
}

// "" when link() is _all alone or names only graphs the registry holds,
// its words read as the renderer reads them (_dash_blank_words); otherwise
// the refusal, without the command's name.  dash.ado compared the value
// inside quotes and split it with Stata's word functions: link(`"g1"x"')
// stopped dash build with r(132) "too few quotes", link(`"g1" "g2"') with
// r(109) "type mismatch", and link(`""g1""') was accepted as g1, where the
// renderer, splitting with str.split(), looks for a graph named "g1",
// quotes and all; and a link(\$m) was accepted as whatever $m held
// (measured 24sep2026; test_json_escaping.cscript JSE-56, JSE-58).  Read
// here by value.
// link()'s groups (WP-31 H2l): the text split at each "||", which
// _dash_extract_links writes between the copies of link().
string rowvector _dash_link_split(string scalar link) {
    string rowvector out
    string scalar    rest
    real scalar      p

    out  = J(1, 0, "")
    rest = link
    while ((p = strpos(rest, "||")) > 0) {
        out  = out, substr(rest, 1, p - 1)
        rest = substr(rest, p + 2, .)
    }
    return((out, rest))
}

string scalar _dash_link_refusal(string scalar link, string scalar registry) {
    string rowvector words, reg, groups, seen
    real scalar      k, g

    if (link == "_all") return("")
    reg    = tokens(registry)
    groups = _dash_link_split(link)
    seen   = J(1, 0, "")
    for (g = 1; g <= cols(groups); g++) {
        words = _dash_blank_words(groups[g])
        for (k = 1; k <= cols(words); k++) {
            // _all links every graph, so beside names, or beside another
            // group, it is a contradiction.
            if (words[k] == "_all") {
                if (cols(groups) > 1) {
                    return("link(_all) links every graph; give it alone.")
                }
                return("link(_all) links every graph; give it alone, or name the graphs to link.")
            }
            if (!anyof(reg, words[k])) {
                return("link() name '" + words[k] + "' not found in registry.")
            }
            if (anyof(seen, words[k])) {
                return("link() name '" + words[k] + "' is in more than one group.")
            }
        }
        seen = seen, words
    }
    return("")
}

// filter with each group's variable replaced by the next of names -- the
// full names of the variables _dash_filter_refusal read, which may have
// been abbreviated -- and the groups joined with " || ".
string scalar _dash_filter_setvars(string scalar filter, string scalar names) {
    string rowvector groups, full, items
    string scalar    out, grp, v
    real scalar      g, c

    groups = _dash_filter_split(filter, 1)
    full   = tokens(names)
    out    = ""
    for (g = 1; g <= cols(groups); g++) {
        grp = groups[g]
        if (g <= cols(full)) {
            items = _dash_filter_items(grp)
            v     = items[1]
            c     = _dash_first_comma_pos(grp)
            if (c > 0) grp = full[g] + substr(grp, c, .)
            else       grp = full[g] + substr(grp, strlen(v) + 1, .)
        }
        out = out + (g > 1 ? " || " : "") + grp
    }
    return(out)
}


// ============================================================
// 8.  JSON STRING VALUE EXTRACTOR
//     _dash_json_get_str(json_str, key, out_macro)
//
// Extracts the value of a JSON string field named `key` from
// `json_str`, correctly handling JSON escape sequences inside
// the value (most importantly \" for embedded double-quotes and
// \\ for literal backslashes).
//
// The naive substr(…, 1, strpos(…, '"') - 1) approach stops at the
// first '"' character even when it is part of a \" escape sequence,
// truncating values that contain quoted strings such as
//     "if_expr": "make == \"AMC Concord\""
//
// This function walks the JSON string value char-by-char, consuming
// escape sequences properly.
//
// Parameters:
//   json_str   : the full JSON text to search
//   key        : the field name WITHOUT surrounding quotes,
//                e.g. "if_expr"
//   out_macro  : Stata local into which the decoded value is stored
//                (empty string if the key is not found)
//
// Called from _dash_plot and _dash_render_immediate in dash.ado.
// ============================================================
void _dash_json_get_str(string scalar json_str,
                        string scalar key,
                        string scalar out_macro) {
    string scalar  needle, s
    real rowvector b, o, u, h
    real scalar    local_pos, n, i, k, c, code, t, d

    // Build search pattern:  "key":"
    needle    = char(34) + key + char(34) + ":" + char(34)
    local_pos = strpos(json_str, needle)
    if (local_pos == 0) {
        st_local(out_macro, "")
        return
    }

    // The value's bytes, from just after its opening quote, decoded in one
    // pass into o -- never longer than the escaped text, so allocated
    // once.  It used to grow the value a character at a time, which is
    // quadratic in its length; a qualifier is read here and may be very
    // long (test_json_escaping.cscript JSE-18, JSE-36).
    //
    // The backslash is byte 92, never the Mata literal "\\": Mata does NOT
    // collapse a doubled backslash in a string literal the way C does --
    // measured, strlen("\\") is 2 and "\\" == char(92) is false.  So every
    // comparison this decoder made with "\\" was a 1-character string
    // against a 2-character one, never true, and it decoded nothing: the
    // first backslash of an escape fell through to the plain-character
    // branch and the '"' after it was read as the closing quote, so
    //     "if_expr": "make == \"AMC Concord\""
    // -- the very case this function was written for -- came back as a
    // single backslash.
    //
    // Every escape JSON has is decoded: \" \\ \/ \b \f \n \r \t and \uXXXX.
    // _dash_json_str writes the backtick, the dollar sign and the
    // apostrophe as JSON escapes, backslash u 0060, 0024 and 0027 (raw,
    // they would end or expand the compound quotes the spec is built in),
    // so a saving() path or a qualifier holding an apostrophe comes back
    // here through one.  An escape that is not JSON's is kept as written.
    b = ascii(substr(json_str, local_pos + strlen(needle), .))
    n = cols(b)
    o = J(1, max((n, 1)), 0)
    k = 0
    i = 1
    while (i <= n) {
        c = b[i]
        if (c == 34) break                  // the closing quote
        if (c != 92 | i == n) {             // a plain byte, or a last backslash
            k++
            o[k] = c
            i++
            continue
        }
        c = b[i + 1]
        d = .
        if      (c == 34)  d = 34
        else if (c == 92)  d = 92
        else if (c == 47)  d = 47           // \/
        else if (c == 98)  d = 8            // \b
        else if (c == 102) d = 12           // \f
        else if (c == 110) d = 10           // \n
        else if (c == 114) d = 13           // \r
        else if (c == 116) d = 9            // \t
        if (d < .) {
            k++
            o[k] = d
            i = i + 2
            continue
        }
        if (c == 117 & i + 5 <= n) {        // \uXXXX
            h = b[|i + 2 \ i + 5|]
            if (all((h :>= 48 :& h :<= 57) :| (h :>= 65 :& h :<= 70) :|
                    (h :>= 97 :& h :<= 102))) {
                code = 0
                for (t = 1; t <= 4; t++) {
                    code = 16 * code + (h[t] <= 57 ? h[t] - 48 :
                                       (h[t] <= 70 ? h[t] - 55 : h[t] - 87))
                }
                // A code Stata cannot hold (NUL) or uchar() cannot write (a
                // lone surrogate) is kept as written.
                s = (code == 0 ? "" : (code < 128 ? char(code) : uchar(code)))
                if (s != "") {
                    u = ascii(s)
                    o[|k + 1 \ k + cols(u)|] = u
                    k = k + cols(u)
                    i = i + 6
                    continue
                }
            }
        }
        k++
        o[k] = 92
        k++
        o[k] = c
        i = i + 2
    }

    st_local(out_macro, (k ? char(o[|1 \ k|]) : ""))
}

// ---------------------------------------------------------------------
// _dash_option_names — the option NAMES in a raw option string.
//
// `_dash_report_ignored' used to split its input with
//     foreach tok of local raw
// which splits on whitespace.  Parentheses are not grouping characters to
// Stata's list handling, so an unsupported option carrying a multi-word
// argument was reported as several options:
//
//     dash scatter y x, addplot(line y2 x)
//     dash: ignoring unsupported option(s): addplot() y2() x)()
//
// naming two options that do not exist.  This walks the string tracking
// paren depth and emits one token per option, its argument consumed with
// it.  A `(' inside a quoted argument does not open a group, so
// label("a (b") cannot unbalance the scan.
// ---------------------------------------------------------------------
// The bare option NAME of one token, with a leading space, or "".
//
// The truncation happens HERE, not on the Stata side: `foreach tok of local'
// re-splits the macro's value on whitespace, so returning
// `addplot(line price weight)' as one token achieved nothing -- Stata took it
// apart again.  Names contain no spaces, so a list of names survives.
string scalar _dash_optname_of(string scalar tok)
{
    string scalar t
    real scalar   ppos

    t = strtrim(tok)
    if (t == "") return("")
    ppos = strpos(t, "(")
    if (ppos > 0) t = strtrim(substr(t, 1, ppos - 1))
    if (t == "") return("")
    return(" " + t)
}

// One pass of the option-name scan.
//
// `track_quotes' is 0 for the fallback pass described in
// _dash_option_names: with an unbalanced quote in the input, honouring
// quotes swallows the rest of the line into a single token and every
// option after the stray '"' is lost from the report.
//
// Sets `unbalanced' to 1 when the pass ended inside a quote.
string scalar _dash_option_names_scan(string scalar raw,
                                      real scalar track_quotes,
                                      real scalar unbalanced)
{
    string scalar out, tok, ch
    real scalar i, n, depth, in_dq, in_cq, nxt

    n     = strlen(raw)
    out   = ""
    tok   = ""
    depth = 0
    in_dq = 0
    in_cq = 0
    i     = 1

    while (i <= n) {
        if (track_quotes) {
            // Consume a quoted run verbatim into the current token so the
            // option's argument stays attached to its key.  The old loop
            // flipped a flag on every '"' with no compound-quote handling,
            // so a compound-quoted value carrying plain quotes came apart.
            nxt = _dash_quote_step(raw, n, i, in_dq, in_cq)
            if (nxt) {
                tok = tok + substr(raw, i, nxt - i)
                i   = nxt
                continue
            }
        }

        ch = substr(raw, i, 1)

        if (ch == "(") {
            depth++
            tok = tok + ch
            i++
            continue
        }
        if (ch == ")") {
            if (depth > 0) depth--
            tok = tok + ch
            i++
            continue
        }
        if (depth == 0 & (ch == " " | ch == char(9))) {
            out = out + _dash_optname_of(tok)
            tok = ""
            i++
            continue
        }
        tok = tok + ch
        i++
    }
    out = out + _dash_optname_of(tok)

    unbalanced = (in_dq | in_cq ? 1 : 0)
    return(strtrim(out))
}

// ============================================================
// _dash_kpi_fields -- the fields a KPI keeps, one global each
// ============================================================
//
// A KPI is a marker global, dash_kpi_<name> = "1", and one global per
// field, dash_kpi_<name>__<field>, for these fields: its statistic,
// variable, value, displayed value, fmt(), title(), subtitle(), color(),
// bgcolor(), update(), its own if and in, and its weight's class and
// variable (WP-31 H2k).  dash.ado's _dash_kpi writes
// them, _dash_prepare_spec reads them and _dash_item_globals retires them;
// test_registry_collision.cscript (REG-25) holds the writer to this list.
//
// The separator is two underscores because no registered name may hold
// two underscores in a row -- _dash_register_graph and _dash_kpi refuse
// one -- so the field globals of KPI a, dash_kpi_a__sta and the rest, are
// no other name's marker or field.  With one underscore they were: a graph
// or a KPI named a_stat took KPI a's statistic (measured 23sep2026 at
// 9f48cf7; see _dash_item_globals).
//
// A field is one to three lower-case letters and never begins with an
// underscore.  A global's name is at most 32 characters: dash_kpi_ (9), an
// 18-character name (the longest _dash_kpi accepts), __ (2) and three
// letters make 32.
//
string rowvector _dash_kpi_fields()
{
    return(("sta", "var", "val", "dsp", "fmt", "tit", "sub", "col",
            "bg", "upd", "if", "in", "wgt", "wex"))
}


// ============================================================
// _dash_item_globals — every global belonging to one registry item
// ============================================================
//
// Graphs and KPIs share one registry and one namespace, and replacing an
// item of one kind with the other has to take the loser's globals with it --
// a name left carrying both a `dash_json_' and a `dash_kpi_' marker is drawn
// as the KPI, so the graph the user just registered would vanish.
//
// An item's globals are these EXACT names and no others: a graph's
// dash_json_<name> and dash_spec_<name>, and a KPI's marker
// dash_kpi_<name> and its fields dash_kpi_<name>__<field>
// (_dash_kpi_fields).  Only the ones Stata holds are returned; an empty
// field is no global at all.  A function graph's points are no global
// (WP-36 plat:PT-4): _dash_drop_item removes their file with
// _dash_fpts_drop.
//
// No prefix is safe.  `macro drop dash_kpi_g1*' also takes g10's globals,
// and g1 and g10 may be registered at once.  This matched dash_kpi_<name>_*
// while a KPI's fields were dash_kpi_<name>_stat, ..., and those were other
// names' globals too: measured 23sep2026 at 9f48cf7, replacing KPI a
// deleted all seven of KPI a_b's globals while the registry still named
// a_b, so the next dash build drew no AB card -- and died with r(7102) on a
// spec whose graphs began "[, {" once a graph was registered after a_b.  A
// prefix on the separator, dash_kpi_<name>__*, is no better: KPI a_'s
// fields, dash_kpi_a___sta and the rest, begin dash_kpi_a__.
//
// The names are compared as strings against what Stata holds, never read
// with st_global(): a name one character past a limit builds a global name
// of 33 characters, and st_global() refuses one with r(3300) (measured
// 23sep2026) -- test_caller_version.cscript asks this about such names.
//
// Returns the names, space separated, in out_macro.
//
void _dash_item_globals(string scalar nm, string scalar out_macro)
{
    string colvector all
    string rowvector own, fld
    string scalar    hit
    real scalar      i, j

    fld = _dash_kpi_fields()
    own = ("dash_json_" + nm, "dash_spec_" + nm, "dash_tu_" + nm,
           "dash_frm_" + nm, "dash_kpi_" + nm)
    // An image panel's marker and fields (WP-33 33-06).
    own = own, ("dash_img_" + nm, "dash_img_" + nm + "__pth",
                "dash_img_" + nm + "__cap", "dash_img_" + nm + "__alt",
                "dash_img_" + nm + "__lnk")
    for (j = 1; j <= length(fld); j++) {
        own = own, "dash_kpi_" + nm + "__" + fld[j]
    }

    hit = ""
    all = st_dir("global", "macro", "dash_*")
    for (i = 1; i <= length(all); i++) {
        for (j = 1; j <= length(own); j++) {
            if (all[i] == own[j]) {
                hit = hit + " " + all[i]
                break
            }
        }
    }
    st_local(out_macro, strtrim(hit))
}


// Reduce raw option text to bare option names, walking with paren depth
// so an option's multi-word argument is consumed with its key.
//
// This runs on the error-reporting path (dash.ado's _dash_report_ignored),
// which means it must never itself fail and must never lose information --
// it is the one place that tells the user what dash ignored.  An odd number
// of double quotes used to leave the scanner stuck inside a quote so every
// option after the stray one vanished from the note:
//     title("unbalanced quote) xlabel(1)   ->   reported only `title'
// When the quote-aware pass ends mid-quote the input cannot be honestly
// quoted, so a second pass reads '"' as an ordinary character.  That
// recovers the remaining option names instead of dropping them.
void _dash_option_names(string scalar in_macro, string scalar out_macro)
{
    string scalar raw, out
    real scalar   unbalanced

    raw        = st_local(in_macro)
    unbalanced = 0

    out = _dash_option_names_scan(raw, 1, unbalanced)
    if (unbalanced) {
        out = _dash_option_names_scan(raw, 0, unbalanced)
    }

    st_local(out_macro, out)
}

// _dash_has_name_opt(s) -- 1 when the option text s holds a name() option.
//
// Stata's -syntax- binds the first name() of an option list to NAMe() and
// leaves any later one in the list's catch-all, so a name() found in the
// catch-all is always a second one -- which twoway refuses, "option name()
// not allowed", r(198).  Options are case-sensitive and NAME() admits the
// spelling name only (WP-31 A3b: nam() and na() are refused by
// _dash_refuse_nam before this is asked), so only it counts: an option
// written NAME() is one dash does not know, and "name(x)" written inside another option's
// argument -- a title(), a note() -- is stepped over, since the scan reads
// top-level option names alone, quotes and parentheses honoured.  Linear in
// the length of s.
real scalar _dash_has_name_opt(string scalar s)
{
    string rowvector names
    real scalar      unbalanced

    unbalanced = 0
    names = tokens(_dash_option_names_scan(s, 1, unbalanced))
    if (unbalanced) names = tokens(_dash_option_names_scan(s, 0, unbalanced))
    if (cols(names) == 0) return(0)
    return(anyof(names, "name"))
}

// _dash_seg_by(seg) -- the value of the last by() a plot segment gives, or
// "" when it gives none.
//
// A segment's options are the text after its first comma outside quotes
// and parentheses; by() is one of them when an option word there is
// spelled by(...) -- BY(), which admits no abbreviation, and options are
// case-sensitive -- with something other than blanks inside.  "by(" written
// in an if's string, a title() or a note() is not an option word and is
// stepped over.  twoway reads the graph's by() from every segment before
// it draws any plot, so dash.ado reads it here before any segment is
// checked (test_parser.cscript P1A-84).  Linear in the length of seg.
string scalar _dash_seg_by(string scalar seg)
{
    string rowvector toks
    string scalar    v, out
    real scalar      pos, j

    pos = _dash_first_comma_pos(seg)
    if (pos == 0) return("")
    toks = _dash_rep_toks(substr(seg, pos + 1, .), 0)
    out  = ""
    for (j = 1; j <= cols(toks); j++) {
        if (_dash_rep_optname(toks[j]) != "by") continue
        v = _dash_rep_value(toks[j])
        if (strtrim(v) != "") out = v
    }
    return(out)
}

// _dash_fn_points_json(yvar, n, x0, dx[, dropxy]) -- a function layer's points, as
// twoway__function_gen made them, as one JSON object (WP-29 P0.6):
// {"x0":<x0>,"dx":<dx>,"y":[<y1>,...,<yn>]}.  x0 and dx are the
// generator's r(min) and r(delta), so x is x0 + dx*(i-1) exactly as the
// generator built it (the renderers rebuild it so, bit for bit; section 04
// E7); y is the first n values of yvar in the generator's order, missing
// as null.  Every number is _dash_json_number17's, so the object holds no
// character but digits, . + - e E, the letters of null, x0, dx and y, and
// " : , { } [ ] -- _dash_fn_spec_tail checks exactly that.
string scalar _dash_fn_points_json(string scalar yvar, real scalar n,
                                   real scalar x0, real scalar dx,
                                   | string scalar dropxy)
{
    string scalar q, dr
    string colvector y
    string rowvector w
    real scalar i

    q = char(34)
    y = _dash_json_number17(st_data((1, n), yvar))
    // WP-31 C5: the generator's r(dropxy), "x y" pairs in double quotes,
    // as "drops":[[x,y],..] -- numbers only, each _dash_json_number17's.
    dr = ""
    if (args() >= 5) {
        w = tokens(subinstr(dropxy, q, " "))
        for (i = 1; i + 1 <= cols(w); i = i + 2) {
            dr = dr + (dr == "" ? "" : ",") + "[" +
                 _dash_json_number17(strtoreal(w[i])) + "," +
                 _dash_json_number17(strtoreal(w[i + 1])) + "]"
        }
    }
    return("{" + q + "x0" + q + ":" + _dash_json_number17(x0) + "," +
           q + "dx" + q + ":" + _dash_json_number17(dx) + "," +
           q + "y" + q + ":[" + invtokens(y', ",") + "]" +
           (dr == "" ? "" : "," + q + "drops" + q + ":[" + dr + "]") + "}")
}

// _dash_fit_points_json(nobs) -- a fit layer's points (WP-31 C4), from
// the data in memory, which hold twoway's serset for the layer (serset
// use): the fitted value first, the two limits next when there are four
// columns, x last.  Written as {"x":[..],"y":[..][,"lo":[..],"hi":[..]],
// "nobs":nobs}, each value %24.17g, a missing one null (_dash_json_number17);
// nobs is the count of the layer's sample, for the renderer's note.
string scalar _dash_fit_points_json(real scalar nobs)
{
    string scalar q, out
    real matrix   D
    real scalar   k

    q = char(34)
    D = st_data(., .)
    k = cols(D)
    if (rows(D) == 0) D = J(0, max((k, 2)), .)
    if (k < 2) return("")
    out = "{" + q + "x" + q + ":[" + invtokens(_dash_json_number17(D[., k])', ",") + "]," +
          q + "y" + q + ":[" + invtokens(_dash_json_number17(D[., 1])', ",") + "]"
    if (k >= 4) {
        out = out + "," + q + "lo" + q + ":[" + invtokens(_dash_json_number17(D[., 2])', ",") + "]," +
              q + "hi" + q + ":[" + invtokens(_dash_json_number17(D[., 3])', ",") + "]"
    }
    return(out + "," + q + "nobs" + q + ":" + _dash_json_number17(nobs) + "}")
}

// _dash_fit_panel_key(vars, gvar, gi) -- the by() values of a group as a
// JSON list (WP-37 stat:PT-12): for each variable of vars, its value at
// the first observation where gvar == gi -- a number as
// _dash_json_number17 writes it; a string variable's value, and a missing
// number's code text ("." or ".a" .. ".z"), as {"s":[<its bytes>]}, so the
// stored table holds no letter _dash_fn_points_ok does not allow.  The
// renderers match it with a panel's own by() values (_dash_by_key_of and
// _dash_fit_panel_spec in dash_render.py).
string scalar _dash_fit_panel_key(string scalar vars, string scalar gvar,
                                  real scalar gi)
{
    string rowvector v
    string scalar    q, out, t
    real colvector   g, at
    real scalar      i, r, x

    q = char(34)
    v = tokens(vars)
    g = st_data(., gvar)
    at = selectindex(g :== gi)
    if (rows(at) == 0) return("[]")
    r = at[1]
    out = ""
    for (i = 1; i <= cols(v); i++) {
        x = 0
        if (st_isstrvar(v[i])) t = _st_sdata(r, st_varindex(v[i]))
        else {
            x = _st_data(r, st_varindex(v[i]))
            if (x >= .) t = strofreal(x)
            else t = ""
        }
        if (st_isstrvar(v[i]) | x >= .) {
            t = "{" + q + "s" + q + ":[" + (t == "" ? "" :
                invtokens(strofreal(ascii(t)), ",")) + "]}"
        }
        else t = _dash_json_number17(x)
        out = out + (i > 1 ? "," : "") + t
    }
    return("[" + out + "]")
}

// _dash_fit_panel_add(sc, key, pts) -- appends {"key":<key>,"points":<pts>}
// to the string scalar named sc, a comma before every entry but the first
// (WP-37 stat:PT-12).
void _dash_fit_panel_add(string scalar sc, string scalar key,
                         string scalar pts)
{
    string scalar q, cur

    q = char(34)
    cur = st_strscalar(sc)
    st_strscalar(sc, cur + (cur == "" ? "" : ",") + "{" + q + "key" + q +
        ":" + key + "," + q + "points" + q + ":" + pts + "}")
}

// _dash_fit_opt_bad(s) -- 1 when the text of estopts(), predopts() or
// estcmd() may not reach a command line (WP-31 C4): a semicolon, a
// backtick, a dollar sign, a line feed or carriage return, an odd number
// of double quotes, or a compound-quote close with no open before it
// (_dash_fn_stray_close).  twoway hands the text to regress, predict or
// fracpoly; dash refuses these before any data are touched.
real scalar _dash_fit_opt_bad(string scalar s)
{
    real scalar i, nq

    if (strpos(s, ";") | strpos(s, char(96)) | strpos(s, char(36)) |
        strpos(s, char(10)) | strpos(s, char(13))) return(1)
    nq = 0
    for (i = 1; i <= strlen(s); i++) nq = nq + (substr(s, i, 1) == char(34))
    if (mod(nq, 2)) return(1)
    return(_dash_fn_stray_close(s))
}

// _dash_recast_canon(name, spellings) -- the full plot-type name that name
// spells among spellings ("full:minimum ..." -- twoway's names and the
// shortest spelling of each, case-sensitive), or "" (WP-31 C4: fitplot()
// and ciplot(); the table is _dash_recast_opt's).
string scalar _dash_recast_canon(string scalar name, string scalar spellings)
{
    string rowvector t
    string scalar    full
    real scalar      i, c, m

    t = tokens(spellings)
    for (i = 1; i <= cols(t); i++) {
        c = strpos(t[i], ":")
        if (!c) continue
        full = substr(t[i], 1, c - 1)
        m = strtoreal(substr(t[i], c + 1, .))
        if (strlen(name) >= m & strlen(name) <= strlen(full) &
            name == substr(full, 1, strlen(name))) return(full)
    }
    return("")
}

// _dash_fn_stray_close(s) -- 1 when s holds a compound-quote close "'
// with no compound open `" before it (counted as a depth), else 0.  twoway's
// parse of its own command line refuses such a function expression, r(198)
// -- y = strlen("'x") -- before twoway__function_gen sees it, and the
// generator alone would take it (WP-29 P0.6, measured); dash refuses it at
// the same point.
real scalar _dash_fn_stray_close(string scalar s)
{
    real scalar i, n, depth
    string scalar two

    n = strlen(s)
    depth = 0
    for (i = 1; i < n; i++) {
        two = substr(s, i, 2)
        if (two == char(96) + char(34)) {
            depth++
            i++
        }
        else if (two == char(34) + char(39)) {
            if (depth == 0) return(1)
            depth--
            i++
        }
    }
    return(0)
}

// _dash_fn_points_ok(txt) -- 1 when txt is a points table dash wrote: it
// begins with {, ends with }, and every byte is one of 0-9 . + - e E n u l
// x d y " : , { } [ ] (an ascii() lookup), or o b s h i, the letters of a
// fit layer's keys lo, hi and nobs (WP-31 C4), or r o p s, which with d
// spell drops (WP-31 C5), or a, which with p n e l s spells panels, a
// by() layer's per-panel points (WP-31 C12), or k and t, which spell a
// fit's per-panel key, points and total (WP-37 stat:PT-12; a key's text
// travels as its bytes, _dash_fit_panel_key).  A global the user set by hand to anything
// else -- }],"graphs":[ among them -- cannot reach the spec.
real scalar _dash_fn_points_ok(string scalar txt)
{
    real rowvector ok, b
    string scalar  allowed

    if (strlen(txt) < 2) return(0)
    if (substr(txt, 1, 1) != "{" | substr(txt, strlen(txt), 1) != "}") return(0)
    allowed = "0123456789.+-eEnulxdyobshirpsakt" + char(34) + ":,{}[]"
    ok = J(1, 256, 0)
    b  = ascii(allowed)
    ok[b :+ 1] = J(1, cols(b), 1)
    b = ascii(txt)
    return(all(ok[b :+ 1]))
}

// A named graph's function points (WP-36 plat:PT-4, DECISIONS A-7): the
// file fp-<hex of the name>.txt in this Stata session's points folder,
// $dash__fpdir, which dash.ado's _dash_fpts_open makes (0700) and in
// which it makes the file (0600, empty) through Python.  A file holds any
// length -- a global holds c(macrolen) characters, and two 10,000-point
// layers are more than half of that -- and outlives clear all, as the
// registry's globals do.  Only these five read, write or remove it.  The
// hex name keeps G and g apart on a file system that ignores case.
string scalar _dash_fpts_path(string scalar nm)
{
    string scalar d

    d = st_global("dash__fpdir")
    if (d == "" | nm == "") return("")
    return(pathjoin(d, "fp-" + invtokens(inbase(16, ascii(nm)), "") + ".txt"))
}

// Replaces the contents of the file _dash_fpts_open made; a graph with no
// file (none made, or the folder gone) is left without points.
void _dash_fpts_put(string scalar nm, string scalar txt)
{
    string scalar p
    real scalar   fh

    p = _dash_fpts_path(nm)
    if (p == "") return
    if (!fileexists(p)) return
    fh = fopen(p, "rw")
    ftruncate(fh)
    if (txt != "") fwrite(fh, txt)
    fclose(fh)
}

// The points of graph nm, or "" when it has no file.
string scalar _dash_fpts_get(string scalar nm)
{
    string scalar p, txt, s
    real scalar   fh

    p = _dash_fpts_path(nm)
    if (p == "") return("")
    if (!fileexists(p)) return("")
    fh = fopen(p, "r")
    txt = ""
    while ((s = fread(fh, 1048576)) != J(0, 0, "")) txt = txt + s
    fclose(fh)
    return(txt)
}

// Removes graph nm's file; none is no error.
void _dash_fpts_drop(string scalar nm)
{
    string scalar p

    p = _dash_fpts_path(nm)
    if (p == "") return
    if (fileexists(p)) (void) _unlink(p)
}

// Removes every graph's file of this session's points folder (dash clear).
void _dash_fpts_clear()
{
    string colvector f
    string scalar    d
    real scalar      i

    d = st_global("dash__fpdir")
    if (d == "") return
    f = dir(d, "files", "fp-*.txt")
    for (i = 1; i <= rows(f); i++) (void) _unlink(pathjoin(d, f[i]))
}

// _dash_fn_spec_tail(path, names, sc) -- close the spec file at path with
// the function points beside the graphs (WP-29 P0.6).
//
// The writers leave the spec's last } off and call this after closing the
// file, so the points -- of any length -- never travel through a macro
// concatenation (a local past c(macrolen) is an uncapturable r(920), and
// st_global() past it truncates in silence; section 04 E6).  With sc != "", the string scalar sc holds the one-line
// graph's table and is the single entry, keyed "" (the graph has no name).
// Otherwise there is one entry "<name>":<points> for each word of names
// whose point file (_dash_fpts_get; WP-36 plat:PT-4) is not empty.  An entry that is not dash's
// (_dash_fn_points_ok) is skipped with a note; the renderers then draw that
// layer as a spec without points, and name what they cannot evaluate
// (WP-30 P1.22).  Appends ,"function_points":{<entries>}} or,
// with no entry, the bare }.  WP-37 TR-13: the contour grids of
// _dash_cg_list, when it has any, go before that } as
// ,"contour_grids":{..} (see the comment in the body).
void _dash_fn_spec_tail(string scalar path, string scalar names,
                        string scalar sc)
{
    external string matrix _dash_cg_list
    string rowvector nm, nmu, ku
    string scalar    q, out, txt, cgt, ent, val, pan, tot, tail
    real scalar      i, fh, j, m, flat

    q   = char(34)
    out = ""
    if (sc != "") {
        txt = st_strscalar(sc)
        // An empty table is a graph with no function layer: nothing to
        // write and nothing to say (it noted every one-line saving()).
        if (txt == "") {}
        else if (_dash_fn_points_ok(txt)) out = q + q + ":" + txt
        else _dash_note("dash: the function points stored for graph '", "",
                        "' are not dash's and are not used; run the graph's " +
                        "dash command again to store Stata's points.")
    }
    else {
        nm = tokens(names)
        for (i = 1; i <= cols(nm); i++) {
            txt = _dash_fpts_get(nm[i])
            if (txt == "") continue
            if (!_dash_fn_points_ok(txt)) {
                _dash_note("dash: the function points stored for graph '",
                           nm[i], "' are not dash's and are not used; run " +
                           "the graph's dash command again to store " +
                           "Stata's points.")
                continue
            }
            out = out + (out == "" ? "" : ",") + q + nm[i] + q + ":" + txt
        }
    }
    // WP-37 TR-13: the contour grids _dash_contour_gen made, as
    // "contour_grids":{"<name>":{"<k>":<object>, ..}, ..}; under by() a
    // layer's value is {"panels":[{"key":<key>,"grid":<object>}, ..],
    // "total":<object>}, in by() group order.  The table is emptied once
    // written.
    cgt = ""
    if (rows(_dash_cg_list) > 0 & cols(_dash_cg_list) == 4) {
        nmu = J(1, 0, "")
        for (i = 1; i <= rows(_dash_cg_list); i++) {
            if (!anyof(nmu, _dash_cg_list[i, 1])) nmu = (nmu, _dash_cg_list[i, 1])
        }
        for (j = 1; j <= cols(nmu); j++) {
            ku = J(1, 0, "")
            for (i = 1; i <= rows(_dash_cg_list); i++) {
                if (_dash_cg_list[i, 1] == nmu[j] & !anyof(ku, _dash_cg_list[i, 2])) {
                    ku = (ku, _dash_cg_list[i, 2])
                }
            }
            ent = ""
            for (m = 1; m <= cols(ku); m++) {
                val = ""
                pan = ""
                tot = ""
                flat = 1
                for (i = 1; i <= rows(_dash_cg_list); i++) {
                    if (_dash_cg_list[i, 1] != nmu[j] | _dash_cg_list[i, 2] != ku[m]) continue
                    if (_dash_cg_list[i, 3] == "") {
                        if (val == "") val = _dash_cg_list[i, 4]
                        continue
                    }
                    flat = 0
                    if (_dash_cg_list[i, 3] == "total") tot = _dash_cg_list[i, 4]
                    else pan = pan + (pan == "" ? "" : ",") + "{" + q + "key" + q + ":" +
                               _dash_cg_list[i, 3] + "," + q + "grid" + q + ":" +
                               _dash_cg_list[i, 4] + "}"
                }
                if (!flat) {
                    val = "{" + q + "panels" + q + ":[" + pan + "]" +
                          (tot == "" ? "" : "," + q + "total" + q + ":" + tot) + "}"
                }
                ent = ent + (ent == "" ? "" : ",") + q + ku[m] + q + ":" + val
            }
            cgt = cgt + (cgt == "" ? "" : ",") + q + nmu[j] + q + ":{" + ent + "}"
        }
    }
    _dash_cg_list = J(0, 4, "")
    tail = ""
    if (out != "") tail = "," + q + "function_points" + q + ":{" + out + "}"
    if (cgt != "") tail = tail + "," + q + "contour_grids" + q + ":{" + cgt + "}"
    fh = fopen(path, "a")
    fwrite(fh, tail + "}")
    fclose(fh)
}

// _dash_cg_reset() -- empty the table of contour grids (WP-37 TR-13).
void _dash_cg_reset()
{
    external string matrix _dash_cg_list
    _dash_cg_list = J(0, 4, "")
}

// _dash_cg_take(name, k, key, cuts, line, frame, n, lframe) -- append the
// contour grid twoway__contour_gen left in frame (columns __cgx __cgy
// __cgz __cgl) to _dash_cg_list as (name, k, key, object), object
// {"cuts":[..],"line":0|1,"x":[..],"y":[..],"z":[..],"levels":[..],
// "n":n} with each value as _dash_json_number17 writes it (null for
// missing), and "lines":{"x","y","z","levels"} from lframe, the
// generator's line output for the boundary lines (D-37-03.h), when lframe
// is not "".  The current frame is restored.
void _dash_cg_take(string scalar name, real scalar k, string scalar key,
                   string scalar cuts, real scalar line, string scalar frame,
                   real scalar n, string scalar lframe)
{
    external string matrix _dash_cg_list
    string scalar    q, cur, obj, part, f
    string rowvector nm
    real colvector   ct
    real matrix      D
    real scalar      i, j

    if (cols(_dash_cg_list) != 4) _dash_cg_list = J(0, 4, "")
    q   = char(34)
    nm  = ("x", "y", "z", "levels")
    ct  = strtoreal(tokens(cuts))'
    cur = st_framecurrent()
    obj = "{" + q + "cuts" + q + ":[" + invtokens(_dash_json_number17(ct)', ",") +
          "]," + q + "line" + q + ":" + strofreal(line != 0)
    for (j = 1; j <= 2; j++) {
        f = (j == 1 ? frame : lframe)
        if (f == "") continue
        st_framecurrent(f)
        D = st_data(., ("__cgx", "__cgy", "__cgz", "__cgl"))
        st_framecurrent(cur)
        part = ""
        for (i = 1; i <= 4; i++) {
            part = part + "," + q + nm[i] + q + ":[" +
                   (rows(D) ? invtokens(_dash_json_number17(D[., i])', ",") : "") + "]"
        }
        if (j == 1) obj = obj + part
        else obj = obj + "," + q + "lines" + q + ":{" + substr(part, 2, .) + "}"
    }
    obj = obj + "," + q + "n" + q + ":" + strofreal(n) + "}"
    _dash_cg_list = _dash_cg_list \ (name, strofreal(k), key, obj)
}

// _dash_unbound_cands(raw, cap) -- the options of a parser's catch-all whose
// value -syntax- may have been unable to bind.
//
// -syntax- leaves an option it declares in the catch-all when it cannot
// bind the value to the declared string: jitter(x"' _dup(3) "INJ" `") is
// one (measured 24sep2026 with syntax [, JITter(string) *]).  twoway
// refuses such a command; dash named the option as unsupported.  A value
// with no double quote in it always binds, so only an option whose text
// holds one, written name(...) with name a Stata name, is a candidate:
// dash.ado's _dash_refuse_unbound then asks the parser itself whether it
// declares the name.  Sets the caller's locals _ru_n (how many, at most
// cap, each option text counted once), _ru_tok<i> (the option's text),
// _ru_nm<i> (its name) and _ru_rc<i> -- twoway's return code for it,
// measured 24sep2026 on sixteen such values: r(109) "type mismatch" when
// the value holds "' (a closing compound quote), otherwise r(198)
// "parentheses do not balance".  Linear in the length of raw.
void _dash_unbound_cands(string scalar raw, real scalar cap)
{
    string scalar    tok, ch, nm, seen
    real scalar      i, n, depth, in_dq, in_cq, nxt, k, p
    string rowvector toks

    n     = strlen(raw)
    toks  = J(1, 0, "")
    tok   = ""
    depth = 0
    in_dq = 0
    in_cq = 0
    i     = 1
    while (i <= n) {
        nxt = _dash_quote_step(raw, n, i, in_dq, in_cq)
        if (nxt) {
            tok = tok + substr(raw, i, nxt - i)
            i   = nxt
            continue
        }
        ch = substr(raw, i, 1)
        if (ch == "(") depth++
        else if (ch == ")") {
            if (depth > 0) depth--
        }
        else if (depth == 0 & (ch == " " | ch == char(9))) {
            if (tok != "") toks = toks, tok
            tok = ""
            i++
            continue
        }
        tok = tok + ch
        i++
    }
    if (tok != "") toks = toks, tok

    k    = 0
    seen = char(0)
    for (i = 1; i <= cols(toks) & k < cap; i++) {
        tok = toks[i]
        if (!strpos(tok, char(34))) continue
        p = strpos(tok, "(")
        if (p < 2 | substr(tok, strlen(tok), 1) != ")") continue
        nm = substr(tok, 1, p - 1)
        if (!_dash_is_name(nm) | strlen(nm) > 32) continue
        if (strpos(seen, char(0) + tok + char(0))) continue
        seen = seen + tok + char(0)
        k++
        st_local("_ru_tok" + strofreal(k), tok)
        st_local("_ru_nm" + strofreal(k), nm)
        st_local("_ru_rc" + strofreal(k),
                 strpos(tok, char(34) + char(39)) ? "109" : "198")
    }
    st_local("_ru_n", strofreal(k))
}

// ============================================================
// Repeated options -- what twoway does with an option given twice
// ============================================================
//
// twoway takes most options more than once ([G-4] Concept: repeated
// options, and measured 24sep2026 by exporting each picture to SVG): a
// RIGHTMOST option draws what its last copy draws -- mcolor(red)
// mcolor(blue) is blue, mc(red) mcolor(blue) too, and an earlier copy is
// never read, so mcolor(bogus) mcolor(red) and mlabel(nosuch) mlabel(make)
// are rc 0; a MERGED option joins its copies -- title(A) title(, color(red))
// draws A in red, xlabel(1 2) xlabel(, angle(45)) the labels 1 2 at 45
// degrees, legend(label(1 "A")) legend(label(2 "B")) both labels, yline(20)
// yline(30) both lines, each in its own style; a UNIQUE option refuses its
// second copy, "option scheme() not allowed", r(198).  dash's -syntax- kept
// the FIRST copy and named the rest as unsupported, or bound a second
// title() to title2() and a second xlabel() to the second axis' xlabel2().
//
// These functions read an option list the way twoway does before -syntax-
// sees it.  dash.ado's _dash_opts_repeats asks the parser itself which
// option each spelling is (so mc and mcolor are one), and
// _dash_rep_reduce writes the list again with one copy of each option:
// the last copy of a rightmost one, the merged value of a merged one.

// _dash_rep_toks(s, commas) -- the top-level words of an option list: runs
// of text split at blanks and tabs outside quotes and parentheses, and at
// commas too when commas is set.  Linear in the length of s: each word is
// cut out by position, and the vector doubles when it fills.
string rowvector _dash_rep_toks(string scalar s, real scalar commas)
{
    string rowvector out
    string scalar    ch
    real scalar      i, n, depth, in_dq, in_cq, nxt, start, k

    n     = strlen(s)
    out   = J(1, 16, "")
    k     = 0
    depth = 0
    in_dq = 0
    in_cq = 0
    start = 0
    i     = 1
    while (i <= n) {
        nxt = _dash_quote_step(s, n, i, in_dq, in_cq)
        if (nxt) {
            if (!start) start = i
            i = nxt
            continue
        }
        ch = substr(s, i, 1)
        if (depth == 0 & (ch == " " | ch == char(9) | (commas & ch == ","))) {
            if (start) {
                if (k == cols(out)) out = out, J(1, cols(out), "")
                out[++k] = substr(s, start, i - start)
                start = 0
            }
            i++
            continue
        }
        if (ch == "(") depth++
        else if (ch == ")" & depth > 0) depth--
        if (!start) start = i
        i++
    }
    if (start) {
        if (k == cols(out)) out = out, J(1, cols(out), "")
        out[++k] = substr(s, start, n - start + 1)
    }
    return(k ? out[|1 \ k|] : J(1, 0, ""))
}

// ---- Stylelists (WP-30 P1.1a) ----
// twoway reads a style option given to a varlist of several y as a
// stylelist ([G-4] stylelists): element k styles the k-th y, "." is the
// default, "=" repeats the element before it ("." when first), ".." and
// "..." -- alone or glued to the end of an element -- repeat it to the
// last y, a short list is padded with ".", extras are ignored, and a
// quoted element is one element.  dash gave every y the whole list, so
// mcolor(red blue) drew two series in the scheme's colours with a note
// (measured 03oct2026, DROPIN-REMAINING.md P1.1).  These functions read
// the list by value; dash.ado's _dash_stylelist_check and
// _dash_plot_opts_to_json call them.

// _dash_stylelist_keys() -- the options read as stylelists, the one list
// of them: the style options (P1.1a; mlpattern WP-31 E2), then the value lists mlabel jitter
// base barwidth (P1.1b), then the named styles pstyle lstyle clstyle mstyle
// mlstyle astyle alstyle bstyle blstyle (P1.14a; p() is one name and is
// not split), dstyle dlstyle bmlinestyle (P1.14b, kept and named) and
// mlabtextstyle (P1.24), then connect cmissing (P1.8a), which
// _dash_connect_opt canonicalises before the per-y writer splits them.
string scalar _dash_stylelist_keys()
{
    return("mcolor msymbol msize msangle mfcolor mlcolor mlwidth mlpattern " +
           "mlabcolor mlabsize mlabposition mlabgap mlabangle mlabformat " +
           "lcolor lwidth lpattern clcolor clpattern clwidth color fcolor " +
           "fintensity bfcolor blcolor acolor alcolor alwidth alpattern " +
           "mlabel jitter base barwidth " +
           "pstyle lstyle clstyle mstyle mlstyle astyle alstyle bstyle blstyle " +
           "dstyle dlstyle bmlinestyle mlabtextstyle connect cmissing")
}

// _dash_stylelist_elems(raw) -- the elements of a stylelist: a 2 x k
// matrix whose row 1 is each element's text and row 2 "1" when it came
// quoted ("..." or `"..."', one level of quotes removed) and "0" when
// bare.  A bare word ending in "..." or ".." (red..., red..) is cut into
// its stem and the repeat, as twoway cuts it (red.... is red. then ...);
// a word of ... alone is the repeat.  A quoted string with a comma glued
// after it ("red",blue) is the string, then the rest from the comma.
// Nothing else is split: ..blue, red...blue, red=blue and (red) stay one
// element each, as twoway reads them.  Linear in the length of raw.
string matrix _dash_stylelist_elems(string scalar raw)
{
    string rowvector toks
    string matrix    out
    string scalar    t, stem, rep, glued
    real scalar      i, n, k, len, p, in_dq, in_cq, q

    toks = _dash_rep_toks(raw, 0)
    n    = cols(toks)
    out  = J(2, 3 * n, "")
    k    = 0
    for (i = 1; i <= n; i++) {
        glued = ""
        t    = toks[i]
        len  = strlen(t)
        stem = t
        rep  = ""
        if (len > 3 & substr(t, len - 2, 3) == "...") {
            stem = substr(t, 1, len - 3)
            rep  = "..."
        }
        else if (len > 2 & t != "..." & substr(t, len - 1, 2) == "..") {
            stem = substr(t, 1, len - 2)
            rep  = ".."
        }
        // One quoted string and nothing else: the quote that opens at 1
        // closes at the last character.
        q   = 0
        len = strlen(stem)
        in_dq = 0
        in_cq = 0
        p = _dash_quote_step(stem, len, 1, in_dq, in_cq)
        if (p & (in_dq | in_cq)) {
            while (p <= len & (in_dq | in_cq)) {
                p = _dash_quote_step(stem, len, p, in_dq, in_cq)
            }
            if (!in_dq & !in_cq & p == len + 1) {
                if (substr(stem, 1, 1) == char(34)) {
                    stem = substr(stem, 2, len - 2)
                }
                else {
                    stem = substr(stem, 3, len - 4)
                }
                q = 1
            }
            // A quoted string with a comma glued after it ("red",blue) is
            // that string: twoway draws mcolor("red",blue) red, silently
            // (WP-31 E5, test/fixtures/colour_width_edges_truth.json
            // sl.quoted_comma).
            else if (!in_dq & !in_cq & p <= len & substr(stem, p, 1) == ",") {
                // The rest, from the comma, is the next element, as
                // twoway reads it: mcolor("red",blue) on two y is
                // "invalid 'blue'", the second y's ",blue" (measured
                // 18oct2026).
                glued = substr(stem, p, .)
                if (substr(stem, 1, 1) == char(34)) {
                    stem = substr(stem, 2, p - 3)
                }
                else {
                    stem = substr(stem, 3, p - 5)
                }
                q = 1
            }
        }
        k++
        out[1, k] = stem
        out[2, k] = (q ? "1" : "0")
        if (glued != "") {
            k++
            out[1, k] = glued
            out[2, k] = "0"
        }
        if (rep != "") {
            k++
            out[1, k] = rep
            out[2, k] = "0"
        }
    }
    return(k ? out[|1, 1 \ 2, k|] : J(2, 0, ""))
}

// _dash_stylelist_norm(raw) -- "" when raw is blank or holds only empty
// quoted elements ("", `""', "" ""), which -syntax-'s string made no
// value; raw unchanged otherwise.  A blank element (" ") is kept, for
// _dash_stylelist_blank to judge.
string scalar _dash_stylelist_norm(string scalar raw)
{
    string matrix E
    real scalar   j

    if (strtrim(raw) == "") return("")
    E = _dash_stylelist_elems(raw)
    for (j = 1; j <= cols(E); j++) {
        if (E[2, j] != "1" | E[1, j] != "") return(raw)
    }
    return("")
}

// _dash_varlabel_tail(raw, i) -- yvarlabel()'s top-level words from the
// i-th on, each as typed (quotes kept), joined by one blank; "" when the
// list is shorter (WP-31 D8).  twoway gives the k-th string to a plot's
// k-th y variable within each of its sersets (measured,
// test/fixtures/varlabel_mlabel_truth.json varlabel.range_two "Band/Top",
// varlabel.fitci "Q/95% CI" and "Q"), and dash writes one record per y of
// an expanded varlist: record i keeps the words from the i-th on, so its
// own y reads the first of them and a range record reads two.
string scalar _dash_varlabel_tail(string scalar raw, real scalar i)
{
    string rowvector t

    if (strtrim(raw) == "" | i < 1) return("")
    t = _dash_rep_toks(raw, 0)
    if (cols(t) < i) return("")
    return(invtokens(t[|1, i \ 1, cols(t)|]))
}

// _dash_stylelist_pick(raw, i) -- the element the i-th y takes, "" for
// the default: "." and a leading "=" are the default, "=" repeats the
// element before it, ".." and "..." repeat it to the last y, a list
// shorter than i gives "", and a quoted element is its text (so "" is
// the default).  Helper _dash_stylelist_elems.
string scalar _dash_stylelist_pick(string scalar raw, real scalar i)
{
    string matrix E
    string scalar prev, v, t
    real scalar   j, bare

    E    = _dash_stylelist_elems(raw)
    prev = ""
    for (j = 1; j <= cols(E); j++) {
        t    = E[1, j]
        bare = (E[2, j] == "0")
        if (bare & (t == ".." | t == "...")) return(prev)
        if (bare & t == "=")      v = prev
        else if (bare & t == ".") v = ""
        // A bare element with an = glued inside or after it (red=blue,
        // red=, T=O) is the default, silently, as twoway draws it (WP-31
        // E4, test/fixtures/colour_width_edges_truth.json sl.eq_glued,
        // sl.eq_trail); one led by = is refused (_dash_stylelist_eqlead).
        else if (bare & strpos(t, "=") > 1) v = ""
        else                      v = t
        if (j == i) return(v)
        prev = v
    }
    return("")
}

// _dash_stylelist_bad(raw) -- 1 when a bare ".." or "..." (glued forms
// included) is not the last element, which twoway refuses as
// "<option>(<value>):  invalid syntax", r(198) (measured 03oct2026).
real scalar _dash_stylelist_bad(string scalar raw)
{
    string matrix E
    real scalar   j

    E = _dash_stylelist_elems(raw)
    for (j = 1; j < cols(E); j++) {
        if (E[2, j] == "0" & (E[1, j] == ".." | E[1, j] == "...")) return(1)
    }
    return(0)
}

// _dash_stylelist_paren(raw) -- twoway's words for the first element
// that opens with "(" -- bare or quoted, mcolor((red)) and
// mcolor("(red)") alike -- as "( red )", one enclosing pair removed and
// the rest trimmed; "" when no element does.  twoway reads such an
// element as an option and refuses it, "option(s) ( red ) not allowed",
// r(198) (WP-31 E4, measured 16oct2026 on mcolor, lcolor, lwidth and
// msymbol; fixture sl.paren).
string scalar _dash_stylelist_paren(string scalar raw)
{
    string matrix E
    string scalar t
    real scalar   j

    E = _dash_stylelist_elems(raw)
    for (j = 1; j <= cols(E); j++) {
        t = strtrim(E[1, j])
        if (substr(t, 1, 1) != "(") continue
        t = substr(t, 2, .)
        if (substr(t, -1, 1) == ")") t = substr(t, 1, strlen(t) - 1)
        t = strtrim(t)
        return(t == "" ? "( )" : "( " + t + " )")
    }
    return("")
}

// _dash_stylelist_eqlead(raw) -- the first bare element led by a glued
// "=" (=blue), "" when none is.  twoway refuses it with an internal class
// path, "color.editstyle invalid name", r(198) (WP-31 E4, measured
// 16oct2026); dash refuses it in its own words, as Q-11.1 refuses a
// blank element.
string scalar _dash_stylelist_eqlead(string scalar raw)
{
    string matrix E
    real scalar   j

    E = _dash_stylelist_elems(raw)
    for (j = 1; j <= cols(E); j++) {
        if (E[2, j] == "0" & strlen(E[1, j]) > 1 & substr(E[1, j], 1, 1) == "=") return(E[1, j])
    }
    return("")
}

// _dash_subopt_colour_comma(value) -- twoway's refusal of the first
// colour sub-option written with commas inside one structured option's
// value (title(), xline(), xlabel(), plotregion(), legend() ...): its
// top-level sub-options, split at blanks and commas outside quotes and
// parentheses, whose name is color, lcolor, labcolor or fcolor (as
// twoway abbreviates them: col, lc, labc, fc) and whose value, one pair
// of enclosing quotes (plain or compound) removed, twoway refuses as
// _dash_colour_comma reads it: "invalid '<word>'", as twoway words it
// (title("T", color("1,2,3")) is "invalid '2'", r(198); WP-31 E5,
// test/fixtures/colour_width_edges_truth.json sc.*; the quotes inside
// count as text, title("T", color("255 0" ,0)) is "invalid '0'",
// measured 18oct2026).  "" when none does.  Text is compared, never run.
string scalar _dash_subopt_colour_comma(string scalar value)
{
    string rowvector toks
    string scalar    nm, v, w
    real scalar      j, p, ok

    toks = _dash_rep_toks(value, 1)
    for (j = 1; j <= cols(toks); j++) {
        nm = strlower(_dash_rep_optname(toks[j]))
        p  = strpos(toks[j], "(")
        if (nm == "" | !p | substr(toks[j], -1, 1) != ")") continue
        ok = (strlen(nm) >= 3 & substr("color", 1, strlen(nm)) == nm)
        ok = ok | (strlen(nm) >= 2 & substr("lcolor", 1, strlen(nm)) == nm)
        ok = ok | (strlen(nm) >= 4 & substr("labcolor", 1, strlen(nm)) == nm)
        ok = ok | (strlen(nm) >= 2 & substr("fcolor", 1, strlen(nm)) == nm)
        if (!ok) continue
        v = strtrim(substr(toks[j], p + 1, strlen(toks[j]) - p - 1))
        if (strlen(v) >= 2 & substr(v, 1, 1) == char(34) & substr(v, -1, 1) == char(34)) {
            v = substr(v, 2, strlen(v) - 2)
        }
        else if (strlen(v) >= 4 & substr(v, 1, 2) == char(96) + char(34) & substr(v, -2, 2) == char(34) + char(39)) {
            v = substr(v, 3, strlen(v) - 4)
        }
        w = _dash_colour_comma(v)
        if (w != "") return("invalid '" + w + "'")
    }
    return("")
}

// _dash_colour_comma(v) -- the word twoway's "invalid '<word>'" names
// for one colour v written with commas, or "" when twoway takes it
// (measured 18oct2026, StataNow 19.5, on five plot options and the
// thirteen structured sub-options of WP-31 E5).  twoway reads v and its
// own " editcopy" after it as parts between commas, every second of
// which must be blank: the first that is not names its first word, a
// closing double quote left off (255,0,0 is '0', red, is 'editcopy',
// 1,,2,3 is '3', red,"blue" is '"blue').  The rest is drawn as its other
// parts joined by blanks (1,,2 is "1 2", noted; the renderer's
// OptionTranslator._colour_commas).  Text is compared, never run.
string scalar _dash_colour_comma(string scalar v)
{
    string scalar t, part, w
    real scalar   k, j

    if (!strpos(v, ",")) return("")
    t = v + " editcopy"
    j = 1
    while (1) {
        k = strpos(t, ",")
        part = strtrim(k ? substr(t, 1, k - 1) : t)
        if (!mod(j, 2) & part != "") {
            w = strpos(part, " ") ? substr(part, 1, strpos(part, " ") - 1) : part
            if (strlen(w) > 1 & substr(w, -1, 1) == char(34)) w = substr(w, 1, strlen(w) - 1)
            return(w)
        }
        if (!k) break
        t = substr(t, k + 1, .)
        j++
    }
    return("")
}

// _dash_stylelist_blank(raw, n) -- the first of the elements the n y
// use that is quoted and blank (" ", `" "'): non-empty text of blanks
// only; 0 when none is.  An empty "" is not blank: twoway reads it as
// ".".  twoway refuses a used blank element with an internal class path
// that differs by option and accepts an unused one (measured 03oct2026);
// Q-11.1 was ratified 06oct2026 as a refusal in dash's own words, used
// elements only.  A missing n or one below 1 reads as 1.
real scalar _dash_stylelist_blank(string scalar raw, real scalar n)
{
    string matrix E
    real scalar   j, m

    m = ((n >= . | n < 1) ? 1 : n)
    E = _dash_stylelist_elems(raw)
    if (cols(E) < m) m = cols(E)
    for (j = 1; j <= m; j++) {
        if (E[2, j] == "1" & E[1, j] != "" & strtrim(E[1, j]) == "") return(j)
    }
    return(0)
}

// _dash_stylelist_blank_words(key) -- the line twoway refuses a used
// blank element of stylelist option key with, r(198): its class path
// with the empty value, written by twoway as an empty macro quote (WP-45
// ST-22, measured 08nov2026, test/fixtures/colour_edges_truth.json B_*;
// the same on every plot type that takes the option).  "" for an option
// twoway accepts a blank element of (pstyle, mstyle, jitter ...) or
// refuses for another reason (mlabel, base, cmissing): dash keeps its own
// words there.  The table's @ is the quote.
string scalar _dash_stylelist_blank_words(string scalar key)
{
    string matrix T
    real scalar   i

    T = ("acolor",         "option(s) area(shadestyle(color(@))  linestyle(color(@))) not allowed" \
         "alcolor",        "option(s) area(linestyle(color(@))) not allowed" \
         "alpattern",      "option(s) area(linestyle(pattern(@))) not allowed" \
         "alstyle",        "option(s) area(linestyle(@)) not allowed" \
         "alwidth",        "option(s) area(linestyle(width(@))) not allowed" \
         "barwidth",       "option barwidth() incorrectly specified" \
         "bfcolor",        "option(s) area(shadestyle(color(@))) not allowed" \
         "blcolor",        "option(s) area(linestyle(color(@))) not allowed" \
         "blstyle",        "option(s) area(linestyle(@)) not allowed" \
         "bmlinestyle",    "option(s) marker(backline(@)) not allowed" \
         "clcolor",        "option(s) line(color(@)) not allowed" \
         "clpattern",      "option(s) line(pattern(@)) not allowed" \
         "clwidth",        "option(s) line(width(@)) not allowed" \
         "color",          "option(s) line(color(@)) area(shadestyle(color(@))) area(linestyle(color(@))) marker(fillcolor(@) linestyle(color(@))) not allowed" \
         "dlstyle",        "option(s) dots(linestyle(@)) not allowed" \
         "fcolor",         "option(s) area(shadestyle(color(@))) not allowed" \
         "fintensity",     "option(s) area(shadestyle(intensity(@))) not allowed" \
         "lcolor",         "option(s) line(color(@)) area(linestyle(color(@))) not allowed" \
         "lpattern",       "option(s) line(pattern(@)) area(linestyle(pattern(@))) not allowed" \
         "lstyle",         "option(s) area(linestyle(@)) not allowed" \
         "lwidth",         "option(s) line(width(@)) area(linestyle(width(@))) not allowed" \
         "mcolor",         "option(s) marker(fillcolor(@)  linestyle(color(@))) not allowed" \
         "mfcolor",        "option(s) marker(fillcolor(@)) not allowed" \
         "mlabangle",      "option(s) label(textstyle(angle(@))) not allowed" \
         "mlabcolor",      "option(s) label(textstyle(color(@))) not allowed" \
         "mlabformat",     "option(s) label(format(@)) not allowed" \
         "mlabgap",        "option(s) label(textgap(@)) not allowed" \
         "mlabposition",   "option(s) label(position(@)) not allowed" \
         "mlabsize",       "option(s) label(textstyle(size(@))) not allowed" \
         "mlabtextstyle",  "option(s) label(textstyle(@)) not allowed" \
         "mlcolor",        "option(s) marker(linestyle(color(@))) not allowed" \
         "mlpattern",      "option(s) marker(linestyle(pattern(@))) not allowed" \
         "mlstyle",        "option(s) marker(linestyle(@)) not allowed" \
         "mlwidth",        "option(s) marker(linestyle(width(@))) not allowed" \
         "msangle",        "option(s) marker(symangle(@)) not allowed" \
         "msize",          "option(s) marker(size(@)) not allowed" \
         "msymbol",        "option(s) marker(symbol(@)) not allowed")
    for (i = 1; i <= rows(T); i++) {
        if (T[i, 1] == key) return(subinstr(T[i, 2], "@", char(96) + char(39)))
    }
    return("")
}

// _dash_stylelist_probe(tok) -- "<name>(x)" when the option word tok is
// <name>(<value>) whose value is no value (_dash_stylelist_norm), so the
// caller can ask the parser which option an empty copy, mcolor(""), is;
// "" otherwise.
string scalar _dash_stylelist_probe(string scalar tok)
{
    string scalar nm

    nm = _dash_rep_optname(tok)
    if (nm == "" | !strpos(tok, "(")) return("")
    if (_dash_stylelist_norm(_dash_rep_value(tok)) != "") return("")
    return(nm + "(x)")
}

// _dash_connect_canon(kind, e) -- one element of connect() (kind
// "connect") or cmissing() (kind "cmissing") as twoway reads it (WP-30
// P1.8a): connect gives direct, ascending, stairstep, stepstair or none,
// cmissing y or n; "" for an empty element and "?" for anything else.
// The spellings are twoway's connectstyle and yesno names as
// test/fixtures/connect_truth.json measures them (its S block):
// case-sensitive (L is ascending, l direct; N and j are unknown); a
// connect element is read by _dash_style_word("connectstyle", e), every
// abbreviation the class's syntax takes (style_words_truth.json, WP-45
// ST-6).  A fixed table read by value; O(len(e)).
string scalar _dash_connect_canon(string scalar kind, string scalar e)
{
    string scalar t
    real scalar   n

    t = strtrim(e)
    if (t == "" | t == ".") return("")
    n = strlen(t)
    if (kind == "cmissing") {
        if (t == "y" | t == "ye" | t == "yes" | t == "on") return("y")
        if (n <= 4 & t == substr("true", 1, n)) return("y")
        if (t == "n" | t == "no" | t == "off") return("n")
        if (n <= 5 & t == substr("false", 1, n)) return("n")
        return("?")
    }
    // connectstyle's reading (WP-45 ST-6): every abbreviation its syntax
    // takes (st, up, no, di, ...), L, J and stairstep_up.
    t = _dash_style_word("connectstyle", t)
    return(t == "" ? "?" : t)
}

// _dash_stylelist_locals(raw, stub) -- the elements of a stylelist as the
// caller's locals: <stub>n their count, <stub>t<j> element j's text and
// <stub>q<j> "1" when it came quoted.  Read and written by value.
void _dash_stylelist_locals(string scalar raw, string scalar stub)
{
    string matrix E
    real scalar   j

    E = _dash_stylelist_elems(raw)
    st_local(stub + "n", strofreal(cols(E)))
    for (j = 1; j <= cols(E); j++) {
        st_local(stub + "t" + strofreal(j), E[1, j])
        st_local(stub + "q" + strofreal(j), E[2, j])
    }
}

// _dash_axis_pieces(s) -- an axis-label option's value split for
// _dash_axis_expand (WP-28 S14, GAPS2 B1).  The head is cut from the tail
// at the first comma outside a string followed by optional blanks and a
// letter or underscore (Stata's sub-option boundary; the ado twin of
// dash_render.py's _dash_axis_head_split).  The head splits, in order,
// into strings (plain or compound, kept whole with their quotes, tag S)
// and the runs of bare text between them (tag B, commas made blanks; tag
// H, left exactly as written, when the run holds a backtick, $ or ' --
// such text never reaches numlist's command line).  The tail, with its
// comma, is last (tag T, possibly empty).  Sets the caller's locals
// _ap_n and, for each piece i, _ap_tag<i> and _ap_txt<i>.
//
// WP-30 P1.18b: the head is rated as twoway reads it, into the caller's
// local _ap_rule (test/fixtures/axis_add_truth.json).  Its first word --
// a quoted string counts as a value -- is a rule when it begins with #,
// is minmax or none, or is a(b)c (a[b]c) with numbers a, b and c; the
// head being that one a(b)c word alone is a lone rule.  _ap_rule is 2
// for a lone rule, 1 for any other rule-led head, 0 for a value first or
// an empty head.  After a rule twoway spends add (ylabel(15(10)35, add)
// draws 15 25 35), so the tail loses every add word when _ap_rule is 1
// or 2; after a lone rule it also loses norescale, which twoway does not
// keep on a range of ticks (ylabel(0(10)100, norescale) widens the
// axis).  The tail is rebuilt from its words (_dash_rep_toks) after one
// comma and blank, "" when none is left.  No regex; linear in s.
void _dash_axis_pieces(string scalar s)
{
    string rowvector tags, txts, hw, tw
    string scalar    head, tail, run, ch, w1, lt
    real scalar      n, i, k, in_dq, in_cq, nxt, was_in, sstart, bstart
    real scalar      rule, p1, p2, cut

    n    = strlen(s)
    head = s
    tail = ""
    in_dq = 0
    in_cq = 0
    i = 1
    while (i <= n) {
        nxt = _dash_quote_step(s, n, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }
        if (substr(s, i, 1) == ",") {
            k = i + 1
            while (k <= n & (substr(s, k, 1) == " " | substr(s, k, 1) == char(9))) k++
            if (k <= n) {
                ch = substr(s, k, 1)
                if (_dash_ascii_in(ch, 65, 90) | _dash_ascii_in(ch, 97, 122) | ch == "_") {
                    head = substr(s, 1, i - 1)
                    tail = substr(s, i, .)
                    break
                }
            }
        }
        i++
    }

    // The head's rating (WP-30 P1.18b).
    rule = 0
    hw   = _dash_rep_toks(subinstr(head, ",", " "), 0)
    if (cols(hw)) {
        w1 = hw[1]
        ch = substr(w1, 1, 1)
        if (ch == char(34) | ch == char(96)) rule = 0
        else if (ch == "#" | w1 == "minmax" | w1 == "none") rule = 1
        else {
            p1 = strpos(w1, "(")
            p2 = strpos(w1, ")")
            if (!p1) {
                p1 = strpos(w1, "[")
                p2 = strpos(w1, "]")
            }
            if (p1 > 1 & p2 > p1 + 1 & p2 < strlen(w1)) {
                if (strtoreal(substr(w1, 1, p1 - 1)) < . &
                    strtoreal(substr(w1, p1 + 1, p2 - p1 - 1)) < . &
                    strtoreal(substr(w1, p2 + 1, .)) < .) {
                    rule = (cols(hw) == 1 ? 2 : 1)
                }
            }
        }
    }
    st_local("_ap_rule", strofreal(rule))
    if (rule & tail != "") {
        tw  = _dash_rep_toks(substr(tail, 2, .), 0)
        lt  = ""
        cut = 0
        for (k = 1; k <= cols(tw); k++) {
            if (tw[k] == "add" | (rule == 2 & tw[k] == "norescale")) {
                cut = 1
                continue
            }
            lt = lt + (lt == "" ? "" : " ") + tw[k]
        }
        if (cut) tail = (lt == "" ? "" : ", " + lt)
    }

    tags = J(1, 0, "")
    txts = J(1, 0, "")
    n = strlen(head)
    in_dq = 0
    in_cq = 0
    sstart = 0
    bstart = 0
    i = 1
    while (i <= n) {
        was_in = (in_dq != 0 | in_cq != 0)
        nxt = _dash_quote_step(head, n, i, in_dq, in_cq)
        if (nxt) {
            if (!was_in) {
                if (bstart) {
                    run = strtrim(substr(head, bstart, i - bstart))
                    if (run != "") {
                        tags = tags, _dash_axis_run_tag(run)
                        txts = txts, (_dash_axis_run_tag(run) == "B" ?
                                      subinstr(run, ",", " ") : run)
                    }
                    bstart = 0
                }
                sstart = i
            }
            if (in_dq == 0 & in_cq == 0 & sstart) {
                tags = tags, "S"
                txts = txts, substr(head, sstart, nxt - sstart)
                sstart = 0
            }
            i = nxt
            continue
        }
        if (!bstart) bstart = i
        i++
    }
    if (sstart) {
        tags = tags, "H"
        txts = txts, substr(head, sstart, .)
    }
    if (bstart) {
        run = strtrim(substr(head, bstart, .))
        if (run != "") {
            tags = tags, _dash_axis_run_tag(run)
            txts = txts, (_dash_axis_run_tag(run) == "B" ?
                          subinstr(run, ",", " ") : run)
        }
    }
    tags = tags, "T"
    txts = txts, tail

    st_local("_ap_n", strofreal(cols(tags)))
    for (i = 1; i <= cols(tags); i++) {
        st_local("_ap_tag" + strofreal(i), tags[i])
        st_local("_ap_txt" + strofreal(i), txts[i])
    }
}

// _dash_axis_run_tag(run) -- "H" when a bare run holds a backtick, $ or '
// (never handed to numlist), else "B".
string scalar _dash_axis_run_tag(string scalar run)
{
    if (strpos(run, char(96)) | strpos(run, "$") | strpos(run, char(39))) return("H")
    return("B")
}

// _dash_axis_fmts(s) -- the format() arguments of an axis-label option's
// sub-option tail, for dash.ado's refusal of a format twoway refuses
// (WP-30 P1.5, M5).  The tail is cut by _dash_axis_pieces' boundary rule;
// its top-level tokens name(arg), outside quotes and parentheses, are read
// when name is lower-case letters, 3 to 6 long, and a prefix of format
// (capitals, fo() and f() are S10's refusals).  Sets the caller's locals
// _af_n (at most 20) and, for each i, _af_raw<i> (the argument as typed,
// trimmed, for the echo), _af_nw<i> (its words once one enclosing pair of
// plain or compound quotes is removed, at most 20), _af_w<i>_<j>, and
// _af_ok<i> (0 when a word fails the gate ^%[A-Za-z0-9_.,:!/+-]+$ or is
// longer than 60 characters, or there are more than 20 words): a word
// reaches confirm format only after the gate.  Linear in strlen(s); never
// calls _stata().
void _dash_axis_fmts(string scalar s)
{
    string scalar    tail, ch, nm, arg, inner
    string rowvector w
    real scalar      n, i, k, in_dq, in_cq, nxt, depth, nstart, astart
    real scalar      cnt, ok, j, nw

    n = strlen(s)
    tail = ""
    in_dq = 0
    in_cq = 0
    i = 1
    while (i <= n) {
        nxt = _dash_quote_step(s, n, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }
        if (substr(s, i, 1) == ",") {
            k = i + 1
            while (k <= n & (substr(s, k, 1) == " " | substr(s, k, 1) == char(9))) k++
            if (k <= n) {
                ch = substr(s, k, 1)
                if (_dash_ascii_in(ch, 65, 90) | _dash_ascii_in(ch, 97, 122) | ch == "_") {
                    tail = substr(s, i + 1, .)
                    break
                }
            }
        }
        i++
    }

    cnt = 0
    n = strlen(tail)
    in_dq = 0
    in_cq = 0
    depth = 0
    nstart = 0
    astart = 0
    nm = ""
    i = 1
    while (i <= n) {
        nxt = _dash_quote_step(tail, n, i, in_dq, in_cq)
        if (nxt) {
            nstart = 0
            i = nxt
            continue
        }
        ch = substr(tail, i, 1)
        if (depth == 0) {
            if (_dash_ascii_in(ch, 65, 90) | _dash_ascii_in(ch, 97, 122) |
                _dash_ascii_in(ch, 48, 57) | ch == "_") {
                if (!nstart) nstart = i
            }
            else if (ch == "(") {
                nm = (nstart ? substr(tail, nstart, i - nstart) : "")
                depth = 1
                astart = i + 1
                nstart = 0
            }
            else nstart = 0
        }
        else if (ch == "(") depth++
        else if (ch == ")") {
            depth--
            if (depth == 0 & cnt < 20 & strlen(nm) >= 3 & strlen(nm) <= 6 &
                regexm(nm, "^[a-z]+$") & substr("format", 1, strlen(nm)) == nm) {
                cnt++
                arg = strtrim(substr(tail, astart, i - astart))
                inner = arg
                if (strlen(inner) >= 2 & substr(inner, 1, 1) == char(34) &
                    substr(inner, -1, 1) == char(34)) {
                    inner = substr(inner, 2, strlen(inner) - 2)
                }
                else if (strlen(inner) >= 4 &
                         substr(inner, 1, 2) == char(96) + char(34) &
                         substr(inner, -2, 2) == char(34) + char(39)) {
                    inner = substr(inner, 3, strlen(inner) - 4)
                }
                w = tokens(inner, " ")
                nw = cols(w)
                ok = (nw <= 20)
                if (nw > 20) nw = 20
                for (j = 1; j <= nw; j++) {
                    if (strlen(w[j]) > 60 | !regexm(w[j], "^%[A-Za-z0-9_.,:!/+-]+$")) ok = 0
                    st_local("_af_w" + strofreal(cnt) + "_" + strofreal(j), w[j])
                }
                st_local("_af_raw" + strofreal(cnt), arg)
                st_local("_af_nw" + strofreal(cnt), strofreal(ok ? nw : 0))
                st_local("_af_ok" + strofreal(cnt), strofreal(ok))
            }
        }
        i++
    }
    st_local("_af_n", strofreal(cnt))
}

// _dash_rep_optname(tok) -- the name an option word was typed with, or ""
// when the word is not an option: name or name(...), name a Stata name of
// at most 32 characters.
string scalar _dash_rep_optname(string scalar tok)
{
    string scalar nm
    real scalar   p

    p  = strpos(tok, "(")
    nm = (p ? substr(tok, 1, p - 1) : tok)
    if (p & substr(tok, strlen(tok), 1) != ")") return("")
    if (!_dash_is_name(nm) | strlen(nm) > 32) return("")
    return(nm)
}

// _dash_rep_value(tok) -- what an option word holds between its outer
// parentheses, exactly as typed (every option merged here is declared
// string asis, so this is the value -syntax- gives it).
string scalar _dash_rep_value(string scalar tok)
{
    real scalar p

    p = strpos(tok, "(")
    if (!p) return("")
    return(substr(tok, p + 1, strlen(tok) - p - 1))
}

// ============================================================
// by()'s grid sub-options refused as twoway refuses them (WP-30 P1.15b)
//
// bygraph_g.class reads by()'s options in three stages (E6, measured on
// StataNow 19.5, test/fixtures/by_grid_truth.json): parse_make's -syntax-
// (:74-81) takes the FIRST copy of each declared option and checks the
// numbers of rows() then cols(); "may not specify both rows() and cols()"
// follows; parse_settings (:266-285) checks holes(); the region, title,
// spacer and bgcolor readers (:224-229) take theirs; and every word left
// over -- a second copy of a word read once, a capitalised spelling, an
// unknown word -- is refused in typed order by -syntax [,
// FAKE_OPT_FOR_BETTER_MSG]- (:232-233), "option NAME[()] not allowed".
// iscale()'s bound is a draw-time error after all of these.
// ============================================================

// _dash_by_grammar() -- twoway's by() grammar, one row per option in
// declaration order: name, minimum, takes an argument, stage, may repeat.
// dash_render.py's _DASH_BY_GRAMMAR is its twin (test_by_grid.py).
string matrix _dash_by_grammar()
{
    string scalar s

    s = ""
    s = s + "total tot 0 1 0 missing miss 0 1 0 rows r 1 1 0 "
    s = s + "colfirst colf 0 1 0 cols c 1 1 0 scale scale 1 1 0 "
    s = s + "iscale iscale 1 1 0 legend leg 1 1 0 legloc legloc 1 1 0 "
    s = s + "plegend pleg 1 1 0 plegloc plegloc 1 1 0 clegend cleg 1 1 0 "
    s = s + "clegloc clegloc 1 1 0 compact com 0 2 0 style style 1 2 0 "
    s = s + "norescale nor 0 2 0 rescale r 0 2 0 noxrescale noxr 0 2 0 "
    s = s + "noyrescale noyr 0 2 0 xrescale xr 0 2 0 yrescale yr 0 2 0 "
    s = s + "holes hol 1 2 0 noedgelabel noedge 0 2 0 edgelabel edge 0 2 0 "
    s = s + "noixaxes noix 0 2 0 noiyaxes noiy 0 2 0 ixaxes ix 0 2 0 "
    s = s + "iyaxes iy 0 2 0 noxtitles noxt 0 2 0 xtitles xt 0 2 0 "
    s = s + "noytitles noyt 0 2 0 ytitles yt 0 2 0 noixlabels noixl 0 2 0 "
    s = s + "noiylabels noiyl 0 2 0 ixlabels ixl 0 2 0 iylabels iyl 0 2 0 "
    s = s + "noixticks noixt 0 2 0 noiyticks noiyt 0 2 0 ixticks ixt 0 2 0 "
    s = s + "iyticks iyt 0 2 0 noixtitles noixt 0 2 0 noiytitles noiyt 0 2 0 "
    s = s + "ixtitles ixt 0 2 0 iytitles iyt 0 2 0 noindividual noind 0 2 0 "
    s = s + "individual ind 0 2 0 ilegends ileg 0 2 0 imargin im 1 2 0 "
    s = s + "noshrink noshr 0 2 0 noishrink noishr 0 2 0 nooverallshrink nooverallshr 0 2 0 "
    s = s + "shrink shr 0 2 0 ishrink ishr 0 2 0 overallshrink overallshr 0 2 0 "
    s = s + "subtitleformat subtitleformat 1 2 0 graphregion graphr 1 3 1 plotregion plotr 1 3 1 "
    s = s + "r1title r1 1 3 1 r2title r2 1 3 1 l1title l1 1 3 1 "
    s = s + "l2title l2 1 3 1 t1title t1 1 3 1 t2title t2 1 3 1 "
    s = s + "b1title b1 1 3 1 b2title b2 1 3 1 note note 1 3 1 "
    s = s + "caption cap 1 3 1 subtitle sub 1 3 1 title t 1 3 1 "
    s = s + "spacers space 1 3 0 bgcolor bgc 1 3 1 "
    return(colshape(tokens(s), 5))
}

// _dash_by_scan(scname) -- read the by() tail in the string scalar scname
// as twoway's three stages do, and set the caller's locals: _byg_rows,
// _byg_cols, _byg_holes, _byg_iscale, _byg_imargin (the first copy's
// argument as typed, "" when absent or empty); _byg_rows_ok, _byg_cols_ok,
// _byg_holes_ok (1 when the argument holds only numlist characters, so
// it may be put to -syntax-); _byg_left (the first leftover in typed
// order, as twoway's message); _byg_iscale_kind (num, star, empty, bad)
// and _byg_iscale_val; _byg_imargin_bad (no marginstyle twoway reads)
// and _byg_imargin_neg (a number below 0).  Words are matched
// case-sensitively; the text is read, never executed, in one pass.
void _dash_by_scan(string scalar scname)
{
    string matrix    g
    string rowvector toks
    string scalar    tok, typed, arg, row, lead, a, w
    real rowvector   seen
    real scalar      j, k, p, paren, n, v
    string rowvector ms, ws

    g = _dash_by_grammar()
    seen = J(1, rows(g), 0)
    toks = _dash_rep_toks(st_strscalar(scname), 0)
    st_local("_byg_left", "")
    for (k = 1; k <= 5; k++) {
        st_local("_byg_" + ("rows", "cols", "holes", "iscale", "imargin")[k], "")
    }
    for (j = 1; j <= cols(toks); j++) {
        tok = toks[j]
        p = strpos(tok, "(")
        paren = (p > 0)
        typed = (paren ? substr(tok, 1, p - 1) : tok)
        arg = (paren ? _dash_rep_value(tok) : "")
        if (paren & substr(tok, strlen(tok), 1) != ")") arg = substr(tok, p + 1, .)
        row = ""
        for (k = 1; k <= rows(g); k++) {
            if (strtoreal(g[k, 3]) != paren) continue
            if (strlen(typed) < strlen(g[k, 2])) continue
            if (substr(typed, 1, strlen(g[k, 2])) != g[k, 2]) continue
            if (substr(g[k, 1], 1, strlen(typed)) != typed) continue
            row = g[k, 1]
            break
        }
        if (row != "") {
            if (seen[k] & g[k, 5] == "0") row = ""
        }
        if (row == "") {
            if (st_local("_byg_left") == "") {
                st_local("_byg_left", "option " + typed + (paren ? "()" : "") + " not allowed")
            }
            continue
        }
        if (seen[k]) continue
        seen[k] = 1
        if (anyof(("rows", "cols", "holes", "iscale", "imargin"), row)) {
            st_local("_byg_" + row, strtrim(arg))
        }
    }
    for (k = 1; k <= 3; k++) {
        a = st_local("_byg_" + ("rows", "cols", "holes")[k])
        st_local("_byg_" + ("rows", "cols", "holes")[k] + "_ok",
                 strofreal(ustrregexm(a, "^[0-9 .eE+/(),:\[\]to-]*$")))
    }
    // iscale(): a number, * and a number, empty, or a text twoway notes
    a = st_local("_byg_iscale")
    lead = ""
    if (substr(a, 1, 1) == "*") {
        lead = "*"
        a = strtrim(substr(a, 2, .))
    }
    v = strtoreal(a)
    if (st_local("_byg_iscale") == "") st_local("_byg_iscale_kind", "empty")
    else if (v < . & ustrregexm(a, "^[-+]?([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][-+]?[0-9]+)?$")) {
        st_local("_byg_iscale_kind", (lead == "*" ? "star" : "num"))
    }
    else st_local("_byg_iscale_kind", "bad")
    st_local("_byg_iscale_val", strofreal(v, "%21.0g"))
    // imargin(): a marginstyle name (dash_render.py SchemeParser._MARGINSTYLES),
    // one to four numbers, or {l|r|b|t}{+|-|=}# terms
    a = st_local("_byg_imargin")
    ms = tokens("10-pt 2-pt 3-pt 4-pt allsides-ms bargraph bottom ebargraph esubhead horiz_bargraph")
    ms = ms, tokens("large left medium medlarge medsmall right side-2-pt side-3-pt side-4-pt sides")
    ms = ms, tokens("small tiny top top_bottom vlarge vside-2-pt vsmall zero")
    st_local("_byg_imargin_bad", "0")
    st_local("_byg_imargin_neg", "0")
    if (a != "" & !anyof(ms, a)) {
        if (ustrregexm(a, "^(\s*[lrbt]\s*[-+=]\s*([0-9]*[.]?[0-9]+)([eE][-+]?[0-9]+)?)+\s*$")) {
        }
        else {
            ws = tokens(a)
            n = cols(ws)
            if (n < 1 | n > 4) st_local("_byg_imargin_bad", "1")
            for (k = 1; k <= n; k++) {
                w = ws[k]
                v = strtoreal(w)
                if (v >= . | !ustrregexm(w, "^[-+]?([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][-+]?[0-9]+)?$")) {
                    st_local("_byg_imargin_bad", "1")
                }
                else if (v < 0) st_local("_byg_imargin_neg", "1")
            }
            if (st_local("_byg_imargin_bad") == "1") st_local("_byg_imargin_neg", "0")
        }
    }
}

// _dash_by_shrinks(tail) -- 1 when the by() tail holds a word twoway reads
// as shrink or overallshrink (both set shrink_plotregion,
// bygraph_g.class:320-331, which refuses aspect() beside it, :559-566),
// else 0 (WP-41 BY-5).  Each token without a parenthesis is matched to
// the first _dash_by_grammar() row as _dash_by_scan matches it, so
// noshrink and ishrink are other rows and note("a shrink b") is text.
real scalar _dash_by_shrinks(string scalar tail)
{
    string matrix    g
    string rowvector toks
    string scalar    tok
    real scalar      j, k

    g = _dash_by_grammar()
    toks = _dash_rep_toks(tail, 0)
    for (j = 1; j <= cols(toks); j++) {
        tok = toks[j]
        if (strpos(tok, "(")) continue
        for (k = 1; k <= rows(g); k++) {
            if (strtoreal(g[k, 3]) != 0) continue
            if (strlen(tok) < strlen(g[k, 2])) continue
            if (substr(tok, 1, strlen(g[k, 2])) != g[k, 2]) continue
            if (substr(g[k, 1], 1, strlen(tok)) != tok) continue
            if (anyof(("shrink", "overallshrink"), g[k, 1])) return(1)
            break
        }
    }
    return(0)
}

// _dash_by_clamp(scname, limit) -- bound by()'s rows() and cols() at the
// by_groups limit (WP-30 P1.15b, TR-48.3, BR-48.7).  In the tail held by
// the string scalar scname, the first copy of rows() and of cols() -- the
// copies twoway reads, matched by _dash_by_grammar() as _dash_by_scan
// matches them -- whose number is above limit is rewritten as the typed
// name and (limit); the rest of the tail is kept byte for byte.  Sets the
// caller's local _byg_clamped to the names changed (rows, cols), "" when
// none.  The text is read and rewritten, never executed, in one pass.
void _dash_by_clamp(string scalar scname, real scalar limit)
{
    string matrix    g
    string rowvector toks
    string scalar    s, tok, typed, row, ch, put, done
    real scalar      j, k, p, cur, start, v, seen_r, seen_c

    g = _dash_by_grammar()
    s = st_strscalar(scname)
    toks = _dash_rep_toks(s, 0)
    done = ""
    seen_r = 0
    seen_c = 0
    cur = 1
    for (j = 1; j <= cols(toks); j++) {
        tok = toks[j]
        // The word's place: _dash_rep_toks cuts each word where the blanks
        // and tabs before it end.
        while (cur <= strlen(s)) {
            ch = substr(s, cur, 1)
            if (ch != " " & ch != char(9)) break
            cur++
        }
        start = cur
        cur = start + strlen(tok)
        p = strpos(tok, "(")
        if (!p) continue
        typed = substr(tok, 1, p - 1)
        row = ""
        for (k = 1; k <= rows(g); k++) {
            if (g[k, 3] != "1") continue
            if (strlen(typed) < strlen(g[k, 2])) continue
            if (substr(typed, 1, strlen(g[k, 2])) != g[k, 2]) continue
            if (substr(g[k, 1], 1, strlen(typed)) != typed) continue
            row = g[k, 1]
            break
        }
        if (row == "rows") {
            seen_r = seen_r + 1
            if (seen_r > 1) continue
        }
        else if (row == "cols") {
            seen_c = seen_c + 1
            if (seen_c > 1) continue
        }
        else continue
        v = strtoreal(strtrim(_dash_rep_value(tok)))
        if (v >= . | v <= limit) continue
        put = typed + "(" + strofreal(limit, "%21.0g") + ")"
        s = substr(s, 1, start - 1) + put + substr(s, cur, .)
        cur = start + strlen(put)
        done = done + (done == "" ? "" : " ") + row
    }
    st_strscalar(scname, s)
    st_local("_byg_clamped", done)
}

// _dash_legend_pos_text(scname) -- the position() text of by()'s keys
// that twoway cannot read as a clock (WP-41 BY-7).  In the tail held by
// the string scalar scname, every legend(), clegend(), plegend(),
// legloc(), clegloc() and plegloc() copy (matched by _dash_by_grammar()
// as _dash_by_scan matches them) is read for its last position()
// (pos() .. position()); the first such text clockdir does not read
// (_dash_style_word: 0-12 as typed and center, top, bottom, left, right
// abbreviated, WP-45 ST-3) -- abc, 13, 03 or 3.0, each "named style ...
// not found in class clockdir" in twoway (by_text_truth.json
// bp77-bp79) -- is returned, ""
// when there is none.  The text is read, never executed, in one pass.
string scalar _dash_legend_pos_text(string scalar scname)
{
    string matrix    g
    string rowvector toks, sub
    string scalar    typed, row, nm, last
    real scalar      j, k, i, p, q

    g = _dash_by_grammar()
    toks = _dash_rep_toks(st_strscalar(scname), 0)
    for (j = 1; j <= cols(toks); j++) {
        p = strpos(toks[j], "(")
        if (p < 2) continue
        typed = substr(toks[j], 1, p - 1)
        row = ""
        for (k = 1; k <= rows(g); k++) {
            if (g[k, 3] != "1") continue
            if (strlen(typed) < strlen(g[k, 2])) continue
            if (substr(typed, 1, strlen(g[k, 2])) != g[k, 2]) continue
            if (substr(g[k, 1], 1, strlen(typed)) != typed) continue
            row = g[k, 1]
            break
        }
        if (!anyof(("legend", "clegend", "plegend", "legloc", "clegloc",
                    "plegloc"), row)) continue
        sub = _dash_rep_toks(_dash_rep_value(toks[j]), 0)
        last = ""
        for (i = 1; i <= cols(sub); i++) {
            q = strpos(sub[i], "(")
            if (q < 2) continue
            nm = substr(sub[i], 1, q - 1)
            if (strlen(nm) >= 3 & nm == substr("position", 1, strlen(nm))) {
                last = strtrim(_dash_rep_value(sub[i]))
            }
        }
        if (last != "" & _dash_style_word("clockdir", last) == "") {
            return(last)
        }
    }
    return("")
}

// _dash_by_plegend_at(scname) -- 1 when the first plegend() copy of the
// by() text held by the string scalar scname (varlist, comma, tail;
// matched by _dash_by_grammar() as _dash_by_scan matches it) names at(#)
// with # >= 1, else 0.  Under coloruseplegend twoway refuses such a
// copy, on or off, with r(4019) (measured 31oct2026; WP-41 K10); at(0)
// and an at() that is not a number are 0.  The text is read, never
// executed.
real scalar _dash_by_plegend_at(string scalar scname)
{
    string matrix    g
    string rowvector toks, sub
    string scalar    s, typed, row, nm, last
    real scalar      j, k, i, p, q, v

    s = st_strscalar(scname)
    p = strpos(s, ",")
    if (!p) return(0)
    g = _dash_by_grammar()
    toks = _dash_rep_toks(substr(s, p + 1, .), 0)
    for (j = 1; j <= cols(toks); j++) {
        p = strpos(toks[j], "(")
        if (p < 2) continue
        typed = substr(toks[j], 1, p - 1)
        row = ""
        for (k = 1; k <= rows(g); k++) {
            if (g[k, 3] != "1") continue
            if (strlen(typed) < strlen(g[k, 2])) continue
            if (substr(typed, 1, strlen(g[k, 2])) != g[k, 2]) continue
            if (substr(g[k, 1], 1, strlen(typed)) != typed) continue
            row = g[k, 1]
            break
        }
        if (row != "plegend") continue
        sub = _dash_rep_toks(_dash_rep_value(toks[j]), 0)
        last = ""
        for (i = 1; i <= cols(sub); i++) {
            q = strpos(sub[i], "(")
            if (q < 2) continue
            nm = substr(sub[i], 1, q - 1)
            if (nm == "at") last = strtrim(_dash_rep_value(sub[i]))
        }
        v = strtoreal(last)
        return(v < . & v >= 1)
    }
    return(0)
}

// _dash_rep_scan(opts, unk, cap) -- whether the list may give an option
// twice, and which spellings to put to the parser.
//
// It may when the parser's catch-all is not empty (unk), or when one
// typed name is another's prefix or the same name: any two spellings of
// one option are both prefixes of its name, so one is the other's prefix.
// (title(A) title(B) never reaches the catch-all: -syntax- binds the second
// to title2(), whose minimum is title.)  A name written bare and written
// with a value are two spellings -- a bare sort is sort, sort(mpg) is
// sort() -- so each is written name or name( here.  Sets the caller's
// locals _rp_go, _rp_n (distinct spellings, at most cap) and, for each,
// _rp_nm<i> and _rp_tok<i>, its last word, which the parser is asked to
// read alone.
void _dash_rep_scan(string scalar opts, real scalar unk, real scalar cap)
{
    string rowvector toks, names, last
    string scalar    nm
    real scalar      i, j, k, go, a, b

    toks  = _dash_rep_toks(opts, 0)
    names = J(1, 0, "")
    last  = J(1, 0, "")
    go    = (unk != 0)
    for (i = 1; i <= cols(toks); i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        nm = nm + (strpos(toks[i], "(") ? "(" : "")
        k = 0
        for (j = 1; j <= cols(names); j++) {
            if (names[j] == nm) {
                k = j
                break
            }
        }
        if (k) {
            // twoway reads sort(varlist) as the rightmost copy that is not
            // empty (_parse combop ..., rightmost skips an empty one:
            // sort(zz) sort() and sort() sort(zz) both sort on zz,
            // measured, WP-29 P0.1 M4), so an empty sort() does not
            // displace a copy with names as the word the parser reads.
            if (!(nm == "sort(" & strtrim(_dash_rep_value(toks[i])) == "" &
                  strtrim(_dash_rep_value(last[k])) != "")) last[k] = toks[i]
            go = 1
            continue
        }
        if (cols(names) >= cap) continue
        names = names, nm
        last  = last, toks[i]
    }
    if (!go) {
        for (i = 1; i <= cols(names) & !go; i++) {
            for (j = 1; j <= cols(names); j++) {
                if (i == j) continue
                a = strlen(subinstr(names[i], "(", ""))
                b = strlen(subinstr(names[j], "(", ""))
                if (a <= b & substr(names[j], 1, a) == substr(names[i], 1, a)) {
                    go = 1
                    break
                }
            }
        }
    }
    st_local("_rp_go", strofreal(go))
    st_local("_rp_n", strofreal(go ? cols(names) : 0))
    if (!go) return
    for (i = 1; i <= cols(names); i++) {
        st_local("_rp_nm" + strofreal(i), names[i])
        st_local("_rp_tok" + strofreal(i), last[i])
    }
}

// _dash_hz_order(opts) -- horizontal and vertical as typed in a plot's
// option list (WP-30 P1.9a): the first word spelling each (minimums hor
// and vert, lower case, no parentheses), in the order typed, as typed:
// "vert hor", one word or "".  dash.ado's _dash_hz_check judges the flags
// in this order and names the word as typed, as twoway names the first
// one it refuses ("option vert not allowed").  The list is read by value;
// nothing in it is run.
string scalar _dash_hz_order(string scalar opts)
{
    string rowvector toks
    string scalar    nm, out
    real scalar      i, h, v

    toks = _dash_rep_toks(opts, 0)
    out = ""
    h = v = 0
    for (i = 1; i <= cols(toks); i++) {
        if (strpos(toks[i], "(")) continue
        nm = _dash_rep_optname(toks[i])
        if (!h & strlen(nm) >= 3 & nm == substr("horizontal", 1, strlen(nm))) {
            out = strtrim(out + " " + nm)
            h = 1
        }
        else if (!v & strlen(nm) >= 4 & nm == substr("vertical", 1, strlen(nm))) {
            out = strtrim(out + " " + nm)
            v = 1
        }
    }
    return(out)
}

// _dash_rep_keyof(snames) -- the option a word read alone set: the s()
// macros the parser left non-empty (snames, from : s(macros)), without its
// catch-all and its pending list, in sorted order; "" when the word left
// anything in the catch-all (it is no option of this parser, or its value
// does not bind).  An option the parser only lists as pending is keyed by
// that list, so sort(a) sort(b) is one option.
string scalar _dash_rep_keyof(string scalar snames)
{
    string rowvector w
    string scalar    key
    real scalar      i

    if (strtrim(st_global("s(_unknown)")) != "") return("")
    w   = sort(tokens(snames)', 1)'
    key = ""
    for (i = 1; i <= cols(w); i++) {
        if (w[i] == "_unknown" | w[i] == "_pending") continue
        // WP-31 D5: aspectratio()'s placement() rides its own key; a copy
        // is keyed as aspectratio() alone.
        if (w[i] == "aspectplacement" | w[i] == "g_aspectplacement") continue
        key = key + (key == "" ? "" : " ") + w[i]
    }
    if (key == "" & strtrim(st_global("s(_pending)")) != "") {
        key = "_p:" + strtrim(st_global("s(_pending)"))
    }
    return(key)
}

// _dash_rep_bare(key) -- the key without the plot parser's g_ prefix.
string scalar _dash_rep_bare(string scalar key)
{
    return(substr(key, 1, 2) == "g_" ? substr(key, 3, .) : key)
}

// _dash_rep_cat(key) -- how twoway treats a repeat of the option: "T" a
// title (merged-explicit: the last text, every copy's sub-options), "L" an
// axis label or tick list (merged-explicit: the last list unless add), "I"
// legend() or a region (merged-implicit), "S" an axis scale (merged-
// implicit, range() the union), "B" by() (the last varlist, every copy's
// sub-options), "X" xline()/yline() (each copy a line of its own), "A"
// text() (each copy added), "F" p() (the first copy: twoway draws
// mcolor(red) p(p3) p(bogus) in p3, WP-30 P1.14a), "H" hover() (dash's
// own: the lists joined, blank-separated, in the order written; its
// reader keeps each variable once, WP-31 A7), "R" everything else
// (the last copy).  The t-options take their x twins' categories (WP-30
// P1.6): tlabel() ttick() tmlabel() tmtick() "L", ttitle() "T", tscale()
// "S", tline() "X", and their axis-2 forms alike.
string scalar _dash_rep_cat(string scalar key)
{
    string scalar k

    k = _dash_rep_bare(key)
    // An axis title's suffix/prefix copy is a line of its own (WP-44
    // MS-13; axis_title_truth.json ms13_*: xtitle, ytitle, ttitle and
    // their axis(2) forms draw A and B on two lines, the edge titles and
    // title() "A B" on one).
    if (anyof(("xtitle", "ytitle", "ttitle", "xtitle2", "ytitle2",
               "ttitle2"), k)) return("TA")
    if (anyof(("title", "subtitle", "note", "caption", "t1title",
               "t2title", "b1title", "b2title", "l1title", "l2title",
               "r1title", "r2title", "ztitle"), k)) return("T")
    if (anyof(("xlabel", "ylabel", "xlabel2", "ylabel2", "xtick", "ytick",
               "xtick2", "ytick2", "xmtick", "ymtick", "xmlabel", "ymlabel",
               "xmtick2", "ymtick2", "xmlabel2", "ymlabel2",
               "zlabel", "tlabel", "ttick", "tmlabel", "tmtick", "tlabel2",
               "ttick2"), k)) return("L")
    if (anyof(("legend", "graphregion", "plotregion"), k)) return("I")
    if (anyof(("xscale", "yscale", "xscale2", "yscale2", "zscale", "tscale",
               "tscale2"), k)) return("S")
    if (k == "by") return("B")
    if (anyof(("xline", "yline", "xline2", "yline2", "tline", "tline2"), k)) return("X")
    if (anyof(("text", "ttext"), k)) return("A")
    if (k == "p") return("F")
    if (k == "hover") return("H")
    return("R")
}

// _dash_rep_unique(key, typed, ptype) -- 1 when twoway refuses a second
// copy of the option on this plot type, "option ...() not allowed",
// r(198).  Measured 24sep2026, each given twice: on every type name()
// saving() scheme() aspectratio() xsize() ysize() scale() fxsize()
// fysize() nodraw play() yaxis() xaxis() colorvar() colordiscrete
// colorcuts() mlabvposition() xoverhangs yoverhangs, a bare sort,
// horizontal and vertical, stdp stdf stdr; bins() discrete fraction
// percent frequency density on histogram; bwidth() (and bw()) and kernel()
// on kdensity lpoly lpolyci lowess; degree() and n() on lpoly and lpolyci;
// mean noweight adjust logit on lowess.  Everything else twoway takes
// more than once.
real scalar _dash_rep_unique(string scalar key, string scalar typed,
                             string scalar ptype)
{
    string scalar k

    k = _dash_rep_bare(key)
    if (anyof(("name", "saving", "scheme", "aspectratio", "xsize", "ysize",
               "scale", "fxsize", "fysize", "nodraw", "play", "yaxis",
               "xaxis", "colorvar", "colordiscrete", "colorcuts",
               "mlabvposition", "xoverhangs", "yoverhangs", "sort",
               "horizontal", "vertical", "stdp", "stdf", "stdr",
               // WP-31 C1: headlabel, now declared, is refused a second
               // time as twoway refuses it ("option headlabel not
               // allowed", r(198), measured 13oct2026).
               "headlabel",
               // WP-31 H2t: dash's own option, taken once.
               "table",
               // GAPS2 X2: colorvarminmax, now declared, is refused a
               // second time as twoway refuses it.  colorlevels() is NOT
               // here: twoway takes it twice (measured 26sep2026).
               "colorvarminmax",
               // WP-31 C2: mwidth, now declared, is taken once on rbar
               // and histogram (measured 13oct2026).
               "mwidth",
               // WP-31 C5: boundary on kdensity and nodropbase (or its
               // dropbase half) on every type, now declared, are taken
               // once: "option boundary not allowed", "option nodropbase
               // not allowed" (kde_hist_fn_truth K08, A02).
               "boundary", "dropbase"), k)) return(1)
    // WP-31 C5: baroffset(), now declared, is taken once on rbar (the row
    // it left in _dash_rep_und_tab, measured 24sep2026) and again on bar
    // and histogram, the rightmost standing (B02, H06).
    if (ptype == "rbar" & k == "baroffset") return(1)
    if (ptype == "histogram" & (typed == "bins" |
        anyof(("discrete", "fraction", "percent", "frequency", "density"), k)))
        return(1)
    if (anyof(("kdensity", "lpoly", "lpolyci", "lowess"), ptype) &
        anyof(("bwidth", "bw", "kernel"), k)) return(1)
    if (anyof(("lpoly", "lpolyci"), ptype) & anyof(("degree", "n"), k))
        return(1)
    if (ptype == "lowess" & anyof(("mean", "noweight", "adjust", "logit"), k))
        return(1)
    return(0)
}

// _dash_rep_und_tab() -- the options dash does not declare that twoway
// takes once (and lowess's logit, whose spellings dash declares only in
// part: see its rows): a second copy is "option atobs not allowed", r(198), naming
// that copy as typed (with "()" when it took a value), or the noX copy of
// an X and noX pair, which are one option.  One row per spelling:
// option, full spelling, shortest spelling, 1 when it takes a value, the
// plot types ("*" every type dash draws), 1 when twoway takes it once from
// the whole graph (a second copy after the paren-mode comma, in another
// plot group or || segment is refused too), and "no" for the noX half of a
// pair.
//
// Measured 24sep2026, every name a twoway parser declares (its class and
// ado files) that dash's parsers leave to the catch-all, on each of the 39
// plot types dash draws: one copy taken, then two refused, on the types
// listed; each shortest spelling taken alone and refused beside the full
// one.  Every other such name twoway takes again (baroffset() on bar,
// mlabgap() anywhere) or does not take once.  A plot option after the
// paren-mode comma is refused by twoway even once, so there only the
// graph-wide rows apply.  The shortest spelling of epan2 is epan2 (ep is
// epanechnikov) and of colorend colore (c is color()).  log is logging
// (noLOGging) on every type, lowess too: twoway takes the graph's options
// out of each list before the plot's parser reads it, so lowess mpg
// weight, log logging is "option logging not allowed".
string matrix _dash_rep_und_tab()
{
    string matrix t
    string scalar fits, cis, kerns, pcs

    fits  = "lfit qfit lfitci qfitci fpfitci"
    cis   = "lfitci qfitci lpolyci fpfitci"
    kerns = "lpoly lpolyci kdensity"
    pcs   = "pcspike pcarrow pcbarrow pcscatter pccapsym pci pcarrowi"
    t = J(0, 7, "")
    // atobs, ciplot(), fitplot(), fit/nofit and smoothplot() are declared
    // since WP-31 C4; their rows stay, as the text twoway refuses a second
    // copy of (measured again 14oct2026, fit_options_truth.json
    // refusals: atobs, nofit, fitplot() and ciplot() given twice are
    // "option ... not allowed", r(198); fit nofit "option nofit not
    // allowed"), and the scan reads the typed text, declared or not.
    t = t \ ("atobs",        "atobs",        "ato",       "0", fits,        "0", "")
    t = t \ ("xlog",         "xlog",         "xlog",      "0", fits,        "0", "")
    t = t \ ("biweight",     "biweight",     "bi",        "0", kerns,       "0", "")
    t = t \ ("cosine",       "cosine",       "cos",       "0", kerns,       "0", "")
    t = t \ ("epan2",        "epan2",        "epan2",     "0", kerns,       "0", "")
    t = t \ ("epanechnikov", "epanechnikov", "ep",        "0", kerns,       "0", "")
    t = t \ ("gaussian",     "gaussian",     "gau",       "0", kerns,       "0", "")
    t = t \ ("parzen",       "parzen",       "par",       "0", kerns,       "0", "")
    t = t \ ("rectangle",    "rectangle",    "rec",       "0", kerns,       "0", "")
    t = t \ ("triangle",     "triangle",     "tri",       "0", kerns,       "0", "")
    t = t \ ("ciplot",       "ciplot",       "cip",       "1", cis,         "0", "")
    t = t \ ("fitplot",      "fitplot",      "fitp",      "1", cis,         "0", "")
    t = t \ ("fit",          "fit",          "fit",       "0", cis,         "0", "")
    t = t \ ("fit",          "nofit",        "nofit",     "0", cis,         "0", "no")
    t = t \ ("back",         "back",         "back",      "0", "mspline mband", "0", "")
    t = t \ ("back",         "noback",       "noback",    "0", "mspline mband", "0", "no")
    t = t \ ("onepanel",     "onepanel",     "onep",      "0", "tsline tsrline", "0", "")
    t = t \ ("pwidth",       "pwidth",       "pw",        "1", "lpolyci",   "0", "")
    t = t \ ("smoothplot",   "smoothplot",   "smoothp",   "1", "lpolyci",   "0", "")
    t = t \ ("var",          "var",          "v",         "1", "lpolyci",   "0", "")
    t = t \ ("weight",       "weight",       "w",         "0", "lowess",    "0", "")
    t = t \ ("colorallowmultiple", "colorallowmultiple", "colorallowmultiple", "0", "*", "0", "")
    t = t \ ("colorend",     "colorend",     "colore",    "1", "*",         "0", "")
    t = t \ ("colorfillonly", "colorfillonly", "colorfillonly", "0", "*",   "0", "")
    t = t \ ("colorformissing", "colorformissing", "colorformiss", "1", "*", "0", "")
    t = t \ ("colorkeysrange", "colorkeysrange", "colorkeysran", "0", "*",  "0", "")
    t = t \ ("colorkeysreverse", "colorkeysreverse", "colorkeysrev", "0", "*", "0", "")
    t = t \ ("colorotherlabel", "colorotherlabel", "colorotherlab", "1", "*", "0", "")
    t = t \ ("colorrule",    "colorrule",    "colorr",    "1", "*",         "0", "")
    t = t \ ("colorstart",   "colorstart",   "colorst",   "1", "*",         "0", "")
    // colorvarminmax left this table (GAPS2 X2): dash now declares it, so
    // a second copy is refused by _dash_rep_unique instead.
    // nodropbase is declared since WP-31 C5 (noDROPBase); these rows stay
    // because -syntax- takes its dropbase half without a trace, so
    // dropbase nodropbase, one option given twice, is caught only here.
    t = t \ ("dropbase",     "dropbase",     "dropb",     "0", "*",         "0", "")
    t = t \ ("dropbase",     "nodropbase",   "nodropb",   "0", "*",         "0", "no")
    t = t \ ("below",        "below",        "below",     "0", "*",         "1", "")
    t = t \ ("clegend",      "clegend",      "cleg",      "1", "*",         "1", "")
    t = t \ ("copyscheme",   "copyscheme",   "copysch",   "0", "*",         "1", "")
    t = t \ ("maxaxes",      "maxaxes",      "maxaxes",   "1", "*",         "1", "")
    t = t \ ("logging",      "logging",      "log",       "0", "*",         "1", "")
    t = t \ ("logging",      "nologging",    "nolog",     "0", "*",         "1", "no")
    // lowess's logit, which dash declares (LOgit): its rows stand after
    // logging's, so log and nolog are read as logging first, as twoway reads
    // them, and lo, logi and logit (nolo, nologi, nologit) as logit.  Listed
    // so lo nolo is one option given twice, "option nolo not allowed", and
    // so a logit spelling after the plot groups' comma is a plot option.
    t = t \ ("logit",        "logit",        "lo",        "0", "lowess",    "0", "")
    t = t \ ("logit",        "nologit",      "nolo",      "0", "lowess",    "0", "no")
    t = t \ ("refscheme",    "refscheme",    "refsch",    "0", "*",         "1", "")
    t = t \ ("refscheme",    "norefscheme",  "norefsch",  "0", "*",         "1", "no")
    t = t \ ("rescaling",    "rescaling",    "rescaling", "0", "*",         "1", "")
    t = t \ ("rescaling",    "norescaling",  "norescaling", "0", "*",       "1", "no")
    t = t \ ("titling",      "titling",      "titling",   "0", "*",         "1", "")
    t = t \ ("titling",      "notitling",    "notitling", "0", "*",         "1", "no")
    t = t \ ("omitallmiss",  "omitallmiss",  "omitallm",  "0", "*",         "1", "")
    t = t \ ("omitanymiss",  "omitanymiss",  "omitanym",  "0", "*",         "1", "")
    t = t \ ("omitdupmiss",  "omitdupmiss",  "omitdup",   "0", "*",         "1", "")
    t = t \ ("omitnothing",  "omitnothing",  "omitn",     "0", "*",         "1", "")
    t = t \ ("pcycle",       "pcycle",       "pcyc",      "1", "*",         "1", "")
    t = t \ ("plegend",      "plegend",      "pleg",      "1", "*",         "1", "")
    return(t)
}

// _dash_rep_und_rows(tab, ptype) -- 1 for each row of tab that applies to
// an option list of plot type ptype, or to the list after the paren-mode
// comma when ptype is "" (the graph-wide rows alone).
real colvector _dash_rep_und_rows(string matrix tab, string scalar ptype)
{
    real colvector ok
    real scalar    r

    ok = J(rows(tab), 1, 0)
    for (r = 1; r <= rows(tab); r++) {
        if (ptype == "") ok[r] = (tab[r, 6] == "1")
        else ok[r] = (tab[r, 5] == "*" | anyof(tokens(tab[r, 5]), ptype))
    }
    return(ok)
}

// _dash_rep_und_row(tok, tab, ok) -- the row of tab that the option word
// tok spells, among the rows ok marks, or 0: its name, as typed (twoway's
// names are lower case, and ATOBS is no spelling of atobs), from the
// row's shortest spelling to its full one, with a value when the row takes
// one and without when it does not.
real scalar _dash_rep_und_row(string scalar tok, string matrix tab,
                              real colvector ok)
{
    string scalar nm
    real scalar   r, L, par

    nm = _dash_rep_optname(tok)
    if (nm == "") return(0)
    par = (strpos(tok, "(") > 0)
    L   = strlen(nm)
    for (r = 1; r <= rows(tab); r++) {
        if (!ok[r] | strtoreal(tab[r, 4]) != par) continue
        if (L < strlen(tab[r, 3]) | L > strlen(tab[r, 2])) continue
        if (substr(tab[r, 2], 1, L) == nm) return(r)
    }
    return(0)
}

// _dash_rep_und_name(t1, p1, t2, p2) -- the copy twoway names when an
// option is given as t1 then t2 (each its name as typed, "()" after it
// when it took a value; p1 and p2 "no" for a noX spelling): the noX copy
// when one copy is X and the other noX, else the second.
string scalar _dash_rep_und_name(string scalar t1, string scalar p1,
                                 string scalar t2, string scalar p2)
{
    if (p1 != p2) return(p1 == "no" ? t1 : t2)
    return(t2)
}

// _dash_rep_und_scan(opts, ptype) -- an option dash does not declare,
// given twice in one option list where twoway takes it once
// (_dash_rep_und_tab): sets the caller's local _rp_refuse to the copy
// twoway names, and to "" when there is none.  Sets the caller's local
// _rp_gund to the graph-wide ones the list gives, one word each,
// option:typed:no-or-dash, for dash.ado to count across the command's
// lists (_dash_rep_und_cross).  Linear in the number of words times the
// rows of the table.
void _dash_rep_und_scan(string scalar opts, string scalar ptype)
{
    string matrix    tab
    string rowvector toks, seen, styped, spol
    string scalar    typed, pol, gund
    real colvector   ok
    real scalar      i, j, r, k

    st_local("_rp_refuse", "")
    st_local("_rp_refuse_g", "0")
    st_local("_rp_gund", "")
    tab  = _dash_rep_und_tab()
    ok   = _dash_rep_und_rows(tab, ptype)
    toks = _dash_rep_toks(opts, 0)
    seen   = J(1, 0, "")
    styped = J(1, 0, "")
    spol   = J(1, 0, "")
    gund   = ""
    for (i = 1; i <= cols(toks); i++) {
        r = _dash_rep_und_row(toks[i], tab, ok)
        if (!r) continue
        typed = _dash_rep_optname(toks[i]) + (tab[r, 4] == "1" ? "()" : "")
        pol   = (tab[r, 7] == "no" ? "no" : "-")
        k = 0
        for (j = 1; j <= cols(seen); j++) {
            if (seen[j] == tab[r, 1]) {
                k = j
                break
            }
        }
        if (k) {
            st_local("_rp_refuse", _dash_rep_und_name(styped[k], spol[k], typed, pol))
            // WP-32: a graph-wide option twoway refuses after the plots'
            // own options and their kernel (_dash_opts_repeats).
            st_local("_rp_refuse_g", tab[r, 6])
            return
        }
        seen   = seen, tab[r, 1]
        styped = styped, typed
        spol   = spol, pol
        if (tab[r, 6] == "1") {
            gund = gund + (gund == "" ? "" : " ") + tab[r, 1] + ":" + typed + ":" + pol
        }
    }
    st_local("_rp_gund", gund)
}

// _dash_rep_und_cross(acc, add) -- the graph-wide options of one more
// option list (the caller's local add, words from _dash_rep_und_scan)
// against those of the lists before it (the caller's local acc): the
// caller's local _rp_refuse names the copy twoway names when one is given
// again, else add's words join acc.
void _dash_rep_und_cross(string scalar acc, string scalar add)
{
    string rowvector a, b, wa, wb
    real scalar      i, j

    st_local("_rp_refuse", "")
    a = tokens(st_local(acc))
    b = tokens(st_local(add))
    for (i = 1; i <= cols(b); i++) {
        wb = tokens(b[i], ":")
        if (cols(wb) != 5) continue
        for (j = 1; j <= cols(a); j++) {
            wa = tokens(a[j], ":")
            if (cols(wa) != 5) continue
            if (wa[1] == wb[1]) {
                st_local("_rp_refuse", _dash_rep_und_name(wa[3], wa[5], wb[3], wb[5]))
                return
            }
        }
    }
    st_local(acc, invtokens((a, b)))
}

// _dash_log_split(src, out) -- the plot parser's option text (the caller's
// local src, ", <options>") without the top-level words log and nolog, and
// those words into the caller's local out.  twoway reads log and nolog as
// the graph option logging (noLOGging) on every plot type, lowess too: it
// takes the graph's options out of a list before the plot's parser reads
// it, so only lo, logi and logit are lowess's logit (measured 24sep2026 on
// lowess, scatter, line, lfit, kdensity and histogram: lowess zb weight,
// log draws the serset of lowess zb weight, and lo, logi and logit that of
// its logit).  -syntax- would bind log, and nolog, to LOgit, so the plot
// parser takes them out first and hands them to its catch-all, as typed.
// src is left alone when neither word is there.  Read by value.
void _dash_log_split(string scalar src, string scalar out)
{
    string rowvector toks, keep, took
    string scalar    s, lead
    real scalar      i

    st_local(out, "")
    s = strtrim(st_local(src))
    lead = ""
    if (substr(s, 1, 1) == ",") {
        lead = ","
        s = substr(s, 2, .)
    }
    toks = _dash_rep_toks(s, 0)
    keep = J(1, 0, "")
    took = J(1, 0, "")
    for (i = 1; i <= cols(toks); i++) {
        if (toks[i] == "log" | toks[i] == "nolog") took = took, toks[i]
        else keep = keep, toks[i]
    }
    if (!cols(took)) return
    st_local(src, lead + " " + invtokens(keep))
    st_local(out, invtokens(took))
}

// _dash_logit_typed(opts) -- the first top-level word of opts that spells
// lowess's logit or its off form, as typed -- lo, logi, logit, nolo,
// nologi, nologit (log and nolog are logging) -- or "".  On any other plot
// type twoway refuses it naming that word, "option lo not allowed",
// r(198) (measured 24sep2026 on scatter, line, lfit, kdensity, histogram).
string scalar _dash_logit_typed(string scalar opts)
{
    string rowvector toks
    real scalar      i

    toks = _dash_rep_toks(opts, 0)
    for (i = 1; i <= cols(toks); i++) {
        if (anyof(("lo", "logi", "logit", "nolo", "nologi", "nologit"),
                  toks[i])) return(toks[i])
    }
    return("")
}

// _dash_barwidth_typed(opts) -- the name of the first top-level option word
// of opts that spells barwidth() -- barw, barwi, barwid, barwidt, barwidth
// -- as typed, or "".  twoway refuses it on rcap and rcapsym naming that
// spelling, "option barw() not allowed", r(198) (measured 03oct2026; WP-30
// P1.17a).  Quoted and nested text is never read: only top-level tokens.
string scalar _dash_barwidth_typed(string scalar opts)
{
    string rowvector toks
    string scalar    nm
    real scalar      i

    toks = _dash_rep_toks(opts, 0)
    for (i = 1; i <= cols(toks); i++) {
        if (!strpos(toks[i], "(")) continue
        nm = _dash_rep_optname(toks[i])
        if (anyof(("barw", "barwi", "barwid", "barwidt", "barwidth"), nm))
            return(nm)
    }
    return("")
}

// _dash_foreign_scan(opts, ptype, unk, graph) -- the option words of a
// list for dash.ado's _dash_refuse_foreign, which asks the parser about
// each.  twoway refuses, even once, an option written in upper case
// (ATOBS, MCOLOR(red), Title(x) -- its names are lower case) and, after
// the plot groups' comma, any plot option (atobs, mcolor(), kernel(), lo),
// "option MCOLOR() not allowed", r(198), naming the first word of the
// list it does not take (measured 24sep2026).  graph is 1 for the list
// after the paren-mode comma (ptype ""), 0 for a plot's list.  Sets the
// caller's local _fs_go to 1 when the parser's catch-all (unk) may hold
// such a word -- any word after the comma, a word in upper case in a
// plot's list -- else 0; and then _fs_n (at most 300 words) and, for each
// option word, _fs_tok<i> (the word), _fs_nm<i> (its name as typed, "()"
// after it when it took a value), _fs_acc<i> (1 when twoway takes it here
// though dash does not declare it: a row of _dash_rep_und_tab), _fs_uc<i>
// (1 when its name is not in lower case) and _fs_plot<i> (1 when it is a
// row of _dash_rep_und_tab for a plot, of any type).  Linear in the words
// times the rows of the table.  Read by value; the words are the user's.
void _dash_foreign_scan(string scalar opts, string scalar ptype,
                        string scalar unk, real scalar graph)
{
    string matrix    tab
    string rowvector toks, u
    string scalar    nm, si
    real colvector   ok, okp
    real scalar      i, n, r, go

    st_local("_fs_n", "0")
    go = 0
    if (graph) go = (strtrim(unk) != "")
    else {
        u = _dash_rep_toks(unk, 0)
        for (i = 1; i <= cols(u) & !go; i++) {
            nm = _dash_rep_optname(u[i])
            if (nm != "" & nm != strlower(nm)) go = 1
        }
    }
    st_local("_fs_go", strofreal(go))
    if (!go) return
    tab  = _dash_rep_und_tab()
    ok   = _dash_rep_und_rows(tab, graph ? "" : ptype)
    okp  = (tab[., 6] :== "0")
    toks = _dash_rep_toks(opts, 0)
    n = 0
    for (i = 1; i <= cols(toks) & n < 300; i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        n++
        si = strofreal(n)
        st_local("_fs_tok" + si, toks[i])
        st_local("_fs_nm" + si, nm + (strpos(toks[i], "(") ? "()" : ""))
        st_local("_fs_acc" + si, strofreal(_dash_rep_und_row(toks[i], tab, ok) > 0))
        st_local("_fs_uc" + si, strofreal(nm != strlower(nm)))
        r = _dash_rep_und_row(toks[i], tab, okp)
        st_local("_fs_plot" + si, strofreal(r > 0))
    }
    st_local("_fs_n", strofreal(n))
}

// _dash_tw_takes_tab() -- the option words twoway takes that dash leaves
// to its catch-all (WP-32): one row per option, its full name, its
// shortest spelling, 1 when it takes a value, the plot types it is taken
// on ("*" every type) and 1 when it is taken after the plot groups'
// comma.  Generated by scripts/gen_twoway_takes_table.py from
// test/fixtures/unknown_option_truth.json (measured 19oct2026: each
// alone on the forty-four types, each shorter spelling, the other form,
// and after the comma).
string matrix _dash_tw_takes_tab()
{
    string matrix t

    t = J(0, 5, "")
    // BEGIN tw_takes (generated by scripts/gen_twoway_takes_table.py from test/fixtures/unknown_option_truth.json; do not edit)
    t = t \ ("afcolor", "afc", "1", "*", "0")
    t = t \ ("afintensity", "afi", "1", "*", "0")
    t = t \ ("alalign", "al", "1", "*", "0")
    t = t \ ("aspect", "aspect", "1", "*", "1")
    t = t \ ("aspectratio", "aspect", "1", "*", "1")
    t = t \ ("atobs", "ato", "0", "lfit qfit lfitci qfitci fpfitci", "0")
    t = t \ ("back", "back", "0", "mspline mband", "0")
    t = t \ ("barbsize", "barbs", "1", "*", "0")
    t = t \ ("bargap", "barg", "1", "area bar spike dropline dot", "0")
    t = t \ ("baroffset", "baroff", "1", "area bar spike dropline dot rbar histogram", "0")
    t = t \ ("bartype", "bart", "1", "area bar spike dropline dot", "0")
    t = t \ ("bcolor", "b", "1", "*", "0")
    t = t \ ("below", "below", "0", "*", "1")
    t = t \ ("bfintensity", "bfi", "1", "*", "0")
    t = t \ ("bgcolor", "bgc", "1", "*", "1")
    t = t \ ("biweight", "bi", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("blalign", "b", "1", "*", "0")
    t = t \ ("blpattern", "b", "1", "*", "0")
    t = t \ ("blwidth", "b", "1", "*", "0")
    t = t \ ("bmcolor", "bmc", "1", "*", "0")
    t = t \ ("bmlalign", "bml", "1", "*", "0")
    t = t \ ("bmlcolor", "bml", "1", "*", "0")
    t = t \ ("bmlpattern", "bml", "1", "*", "0")
    t = t \ ("bmlwidth", "bml", "1", "*", "0")
    t = t \ ("bmsize", "bms", "1", "*", "0")
    t = t \ ("bmsymbol", "bms", "1", "*", "0")
    t = t \ ("boundary", "boundary", "0", "kdensity", "0")
    t = t \ ("bsymbol", "b", "1", "*", "0")
    t = t \ ("ciplot", "cip", "1", "lfitci qfitci fpfitci lpolyci", "0")
    t = t \ ("clalign", "cla", "1", "*", "0")
    t = t \ ("clegend", "cleg", "1", "*", "1")
    t = t \ ("colorallowmultiple", "colorallowmultiple", "0", "*", "0")
    t = t \ ("colorend", "c", "1", "*", "0")
    t = t \ ("colorfillonly", "colorfillonly", "0", "*", "0")
    t = t \ ("colorformissing", "colorformiss", "1", "*", "0")
    t = t \ ("colorkeysrange", "colorkeysran", "0", "*", "0")
    t = t \ ("colorkeysreverse", "colorkeysrev", "0", "*", "0")
    t = t \ ("colorotherlabel", "colorotherlab", "1", "*", "0")
    t = t \ ("colorrule", "c", "1", "*", "0")
    t = t \ ("colorstart", "colorst", "1", "*", "0")
    t = t \ ("copyscheme", "copysch", "0", "*", "1")
    t = t \ ("cosine", "cos", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("dcolor", "d", "1", "*", "0")
    t = t \ ("dfcolor", "dfc", "1", "*", "0")
    t = t \ ("dlcolor", "d", "1", "*", "0")
    t = t \ ("dlpattern", "d", "1", "*", "0")
    t = t \ ("dlstyle", "d", "1", "*", "0")
    t = t \ ("dlwidth", "d", "1", "*", "0")
    t = t \ ("dotextend", "dotex", "1", "area bar spike dropline dot", "0")
    t = t \ ("dropbase", "dropb", "0", "*", "0")
    t = t \ ("droplines", "drop", "1", "function", "0")
    t = t \ ("dropto", "drop", "1", "area bar spike dropline dot", "0")
    t = t \ ("dsize", "d", "1", "*", "0")
    t = t \ ("dstyle", "d", "1", "*", "0")
    t = t \ ("dsymbol", "d", "1", "*", "0")
    t = t \ ("epan2", "ep", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("epanechnikov", "ep", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("estcmd", "est", "1", "fpfit fpfitci", "0")
    t = t \ ("estopts", "est", "1", "lfit qfit lfitci qfitci fpfit fpfitci", "0")
    t = t \ ("fit", "fit", "0", "lfitci qfitci fpfitci lpolyci", "0")
    t = t \ ("fitplot", "fitp", "1", "lfitci qfitci fpfitci lpolyci", "0")
    t = t \ ("fxsize", "fxsiz", "1", "*", "1")
    t = t \ ("fysize", "fysiz", "1", "*", "1")
    t = t \ ("gap", "gap", "1", "histogram", "0")
    t = t \ ("gaussian", "gau", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("graphregion", "graphr", "1", "*", "1")
    t = t \ ("headlabel", "head", "0", "rpcap rpspike pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi", "0")
    t = t \ ("heatlabel", "heatlabel", "0", "contour contourline", "0")
    t = t \ ("lalign", "l", "1", "*", "0")
    t = t \ ("logging", "log", "0", "*", "1")
    t = t \ ("mangle", "mang", "1", "*", "0")
    t = t \ ("maxaxes", "maxaxes", "1", "*", "1")
    t = t \ ("mlabalignment", "mlabalign", "1", "*", "0")
    t = t \ ("mlabels", "m", "1", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike contour contourline pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci kdensity histogram function", "0")
    t = t \ ("mlabjustification", "mlabjust", "1", "*", "0")
    t = t \ ("mlabprefix", "mlabpre", "1", "*", "0")
    t = t \ ("mlabstyle", "mlabs", "1", "*", "0")
    t = t \ ("mlabsuffix", "mlabsuff", "1", "*", "0")
    t = t \ ("mlalign", "mlal", "1", "*", "0")
    t = t \ ("msymangle", "msyman", "1", "*", "0")
    t = t \ ("mwidth", "mw", "0", "rbar histogram", "0")
    t = t \ ("ndots", "ndot", "1", "area bar spike dropline dot", "0")
    t = t \ ("noback", "noback", "0", "mspline mband", "0")
    t = t \ ("nodropbase", "nodropb", "0", "*", "0")
    t = t \ ("nofit", "nofit", "0", "lfitci qfitci fpfitci lpolyci", "0")
    t = t \ ("nologging", "nolog", "0", "*", "1")
    t = t \ ("norefscheme", "norefsch", "0", "*", "1")
    t = t \ ("norescaling", "norescaling", "0", "*", "1")
    t = t \ ("notitling", "notitling", "0", "*", "1")
    t = t \ ("numkeys", "numkey", "1", "*", "0")
    t = t \ ("omitallmiss", "omitallm", "0", "*", "1")
    t = t \ ("omitanymiss", "omitanym", "0", "*", "1")
    t = t \ ("omitdupmiss", "omitdup", "0", "*", "1")
    t = t \ ("omitnothing", "omitn", "0", "*", "1")
    t = t \ ("onepanel", "onep", "0", "tsline tsrline", "0")
    t = t \ ("parzen", "par", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("pcycle", "pcyc", "1", "*", "1")
    t = t \ ("play", "play", "1", "", "1")
    t = t \ ("plegend", "pleg", "1", "*", "1")
    t = t \ ("plotregion", "plotr", "1", "*", "1")
    t = t \ ("predopts", "pred", "1", "lfit qfit lfitci qfitci", "0")
    t = t \ ("pwidth", "p", "1", "lpolyci", "0")
    t = t \ ("rectangle", "rec", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("refscheme", "refsch", "0", "*", "1")
    t = t \ ("rescaling", "rescaling", "0", "*", "1")
    t = t \ ("scale", "scale", "1", "*", "1")
    t = t \ ("scheme", "sch", "1", "*", "1")
    t = t \ ("titling", "titling", "0", "*", "1")
    t = t \ ("tlabel", "t", "1", "*", "1")
    t = t \ ("tline", "t", "1", "*", "1")
    t = t \ ("tmlabel", "tml", "1", "*", "1")
    t = t \ ("tmtick", "tmt", "1", "*", "1")
    t = t \ ("triangle", "tri", "0", "lpoly lpolyci kdensity", "0")
    t = t \ ("tscale", "tsc", "1", "*", "1")
    t = t \ ("ttick", "t", "1", "*", "1")
    t = t \ ("ttitle", "t", "1", "*", "1")
    t = t \ ("var", "v", "1", "lpolyci", "0")
    t = t \ ("xaxis", "xax", "1", "*", "0")
    t = t \ ("xlog", "xlog", "0", "lfit qfit lfitci qfitci fpfitci", "0")
    t = t \ ("xoverhangs", "xoverhang", "0", "*", "1")
    t = t \ ("xsize", "xsiz", "1", "*", "1")
    t = t \ ("xtransform", "xt", "1", "lfit qfit lfitci qfitci fpfitci", "0")
    t = t \ ("xvarlabel", "xvarl", "1", "*", "0")
    t = t \ ("yaxis", "yax", "1", "*", "0")
    t = t \ ("yoverhangs", "yoverhang", "0", "*", "1")
    t = t \ ("ysize", "ysiz", "1", "*", "1")
    t = t \ ("yvarlabel", "yvarl", "1", "*", "0")
    t = t \ ("zlabel", "zl", "1", "*", "1")
    t = t \ ("zmlabel", "zml", "1", "*", "1")
    t = t \ ("zmtick", "zmt", "1", "*", "1")
    t = t \ ("zscale", "zsc", "1", "*", "1")
    t = t \ ("ztick", "zt", "1", "*", "1")
    t = t \ ("ztitle", "zt", "1", "*", "1")
    t = t \ ("zvarformat", "zvarf", "1", "*", "0")
    t = t \ ("zvarlabel", "zvarl", "1", "*", "0")
    // END tw_takes
    return(t)
}

// _dash_tw_takes(tok, ptype, graph) -- 1 when twoway takes the option
// word tok on plot type ptype (graph 1: after the plot groups' comma),
// though dash does not declare it: a row of _dash_tw_takes_tab or of
// _dash_rep_und_tab, spelled from its shortest spelling to its full name,
// with a value when it takes one; and mlabfontface()'s spellings (mlabfon
// and longer), which twoway refuses later, in its own words
// (_dash_refuse_mlabff).  Its name as typed: twoway's names are lower case.
real scalar _dash_tw_takes(string scalar tok, string scalar ptype,
                           real scalar graph)
{
    string matrix t
    string scalar nm
    real colvector ok
    real scalar   r, L, par

    nm = _dash_rep_optname(tok)
    if (nm == "") return(0)
    par = (strpos(tok, "(") > 0)
    L   = strlen(nm)
    if (L >= 7 & L <= 12 & substr("mlabfontface", 1, L) == nm) return(1)
    t = _dash_tw_takes_tab()
    for (r = 1; r <= rows(t); r++) {
        if (strtoreal(t[r, 3]) != par) continue
        if (L < strlen(t[r, 2]) | L > strlen(t[r, 1])) continue
        if (substr(t[r, 1], 1, L) != nm) continue
        if (graph) {
            if (t[r, 5] == "1") return(1)
        }
        else if (t[r, 4] == "*" | anyof(tokens(t[r, 4]), ptype)) return(1)
    }
    t  = _dash_rep_und_tab()
    ok = _dash_rep_und_rows(t, graph ? "" : ptype)
    return(_dash_rep_und_row(tok, t, ok) > 0)
}

// _dash_omit_pair(opts, ptypes) -- twoway's refusal of two omit options
// in one command (WP-35 basic:PT-8): "" unless the bare words of the
// option text opts that reach omitanymiss, omitallmiss, omitdupmiss or
// omitnothing from their minimum (omitanym, omitallm, omitdup, omitn)
// occur twice or more and one of the plot types ptypes is a type twoway
// checks them on; then the message word, the distinct words in full, in
// that order, joined with no blank -- "omitanymissomitallmiss" for
// omitallmiss omitanymiss, "omitanymiss" for the word twice (measured,
// test/fixtures/graph_refusal_truth.json omit.*).  lfit, lfitci, qfit,
// qfitci, fpfit, fpfitci, scatteri, pci and pcarrowi alone take a pair.
string scalar _dash_omit_pair(string scalar opts, string scalar ptypes)
{
    string rowvector tok, w, m, pt
    string scalar    t, out
    real rowvector   seen
    real scalar      i, j, n, L, chk

    pt  = tokens(ptypes)
    chk = 0
    for (i = 1; i <= cols(pt); i++) {
        if (!anyof(("lfit", "lfitci", "qfit", "qfitci", "fpfit", "fpfitci",
                    "scatteri", "pci", "pcarrowi"), pt[i])) chk = 1
    }
    if (!chk) return("")
    w    = ("omitanymiss", "omitallmiss", "omitdupmiss", "omitnothing")
    m    = ("omitanym", "omitallm", "omitdup", "omitn")
    seen = J(1, 4, 0)
    n    = 0
    tok  = _dash_opt_tokens(opts)
    for (i = 1; i <= cols(tok); i++) {
        t = tok[i]
        L = strlen(t)
        for (j = 1; j <= 4; j++) {
            if (L >= strlen(m[j]) & L <= strlen(w[j]) &
                substr(w[j], 1, L) == t) {
                seen[j] = 1
                n++
            }
        }
    }
    if (n < 2) return("")
    out = ""
    for (j = 1; j <= 4; j++) if (seen[j]) out = out + w[j]
    return(out)
}

// _dash_maxaxes_val(text, opt) -- the value of the last top-level copy of
// opt -- maxaxes (full spelling only, as twoway's MAXAXES()), yaxis or
// xaxis (yax and longer) -- in the option text text, trimmed; "" when it
// is not there (WP-35 GW-3; graph_refusal_truth.json maxaxes.*).  With opt
// "drop": text less every maxaxes() copy, its other options as typed, one
// blank between them (a valid maxaxes() is taken out of the note).
string scalar _dash_maxaxes_val(string scalar text, string scalar opt)
{
    string rowvector tok
    string scalar    t, nm, out, kept, o
    real scalar      i, p, L, lo

    o    = (opt == "drop" ? "maxaxes" : opt)
    lo   = (o == "maxaxes" ? 7 : 3)
    out  = ""
    kept = ""
    tok  = _dash_opt_tokens(text)
    for (i = 1; i <= cols(tok); i++) {
        t = tok[i]
        p = strpos(t, "(")
        nm = (p ? substr(t, 1, p - 1) : "")
        L  = strlen(nm)
        if (!p | substr(t, strlen(t), 1) != ")" | L < lo | L > strlen(o) |
            substr(o, 1, L) != nm) {
            kept = kept + (kept == "" ? "" : " ") + t
            continue
        }
        out = strtrim(substr(t, p + 1, strlen(t) - p - 1))
    }
    return(opt == "drop" ? kept : out)
}

// _dash_tw_refuses_tab() -- the options dash declares that twoway refuses
// (WP-32, BUGS.md "dash names in its note, as not drawn, options twoway
// refuses on that plot type"): at(), blabel(), ciopts(), fitopts(),
// lineopts(), mlabwidth(), filter() and link() on every type and filter()
// and link() after the plot groups' comma, "option at() not allowed",
// r(198); headlabel off the paired-coordinate types (measured 19oct2026,
// test/fixtures/noted_option_truth.json).  dash named each in its note as
// not drawn.  One row each: its full name, the shortest spelling dash's
// -syntax- binds to it, the types twoway refuses it on ("*" for all
// forty-four) and 1 when twoway refuses it after the comma.
string matrix _dash_tw_refuses_tab()
{
    string matrix t

    t = J(0, 4, "")
    // BEGIN tw_refuses (generated by scripts/gen_twoway_takes_table.py from test/fixtures/noted_option_truth.json; do not edit)
    t = t \ ("at", "at", "*", "0")
    t = t \ ("blabel", "blabel", "*", "0")
    t = t \ ("ciopts", "ciopts", "*", "0")
    t = t \ ("filter", "filt", "*", "1")
    t = t \ ("fitopts", "fitopts", "*", "0")
    t = t \ ("headlabel", "head", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter contour contourline scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function", "0")
    t = t \ ("lineopts", "lineopts", "*", "0")
    t = t \ ("link", "link", "*", "1")
    t = t \ ("mlabwidth", "mlabw", "*", "0")
    // END tw_refuses
    return(t)
}

// ============================================================
// p1() .. p20() (WP-35 syn:SD-3).  twoway hands p<k>() after the plot
// groups' comma to its k-th plot, each y of a varlist counted, a ci fit
// once (twowaygraph_g.class get_plot_count), and p<j>() inside one plot's
// options to that plot's j-th y (twoway_yxview_parse.class); a number
// above 20 is "p21(...):  too many arguments", r(103), after the comma
// and inside a plot (measured 26oct2026, test/fixtures/pnum_truth.json
// g_p3, multi_y, ci_p2, g_p21, g_p100, own_p21).  dash noted p1(), p2()
// and p20() and drew nothing, and refused p3() .. p19().

// _dash_p_take(opts) -- opts less its p<k>() words: p, a number from 1
// with no leading zero, then a value in parentheses, lower case only (so
// the whole-plot p() is left alone).  Sets the caller's locals _pt_n (how
// many were taken), _pt_pairs ("<k>:<value>" for each, in the order
// typed, joined by char(1)) and _pt_bad (the first word whose number is
// above 20, as typed, cut to 80 characters; "" for none).  opts comes
// back unchanged when it holds no such word, else its other words joined
// by one blank.
string scalar _dash_p_take(string scalar opts)
{
    string rowvector toks
    string scalar    out, pairs, bad, t
    real scalar      i, k, n, p

    st_local("_pt_n", "0")
    st_local("_pt_pairs", "")
    st_local("_pt_bad", "")
    if (!ustrregexm(opts, "(^|\s)p[1-9][0-9]*\(")) return(opts)
    toks  = _dash_opt_tokens(opts)
    out   = ""
    pairs = ""
    bad   = ""
    n     = 0
    for (i = 1; i <= cols(toks); i++) {
        t = toks[i]
        if (!ustrregexm(t, "^p([1-9][0-9]*)\(") | substr(t, strlen(t), 1) != ")") {
            out = out + (out == "" ? "" : " ") + t
            continue
        }
        k = strtoreal(ustrregexs(1))
        p = strpos(t, "(")
        if (k > 20) {
            if (bad == "") bad = substr(t, 1, 80)
            continue
        }
        n++
        pairs = pairs + (pairs == "" ? "" : char(1)) + strofreal(k) + ":" +
                substr(t, p + 1, strlen(t) - p - 1)
    }
    st_local("_pt_n", strofreal(n))
    st_local("_pt_pairs", pairs)
    st_local("_pt_bad", bad)
    return(out)
}

// _dash_p_key(tok) -- the stylelist option (_dash_stylelist_keys) the
// option word tok binds to, or "": its name of length L matches a row
// when L is at least the row's minimum and the full name starts with it.
// The minimums are the capitals of _dash_parse_plot_opts's declarations
// (test/test_pnum.py checks them).
string scalar _dash_p_key(string scalar tok)
{
    string matrix t
    string scalar nm
    real scalar   r, L

    nm = _dash_rep_optname(tok)
    L  = strlen(nm)
    if (!L) return("")
    t = ("mcolor", "mc" \ "msymbol", "m" \ "msize", "msi" \
         "msangle", "msa" \ "mfcolor", "mfc" \ "mlcolor", "mlc" \
         "mlwidth", "mlw" \ "mlpattern", "mlp" \ "mlabcolor", "mlabc" \
         "mlabsize", "mlabs" \ "mlabposition", "mlabp" \
         "mlabgap", "mlabg" \ "mlabangle", "mlabang" \
         "mlabformat", "mlabf" \ "lcolor", "lc" \ "lwidth", "lw" \
         "lpattern", "lp" \ "clcolor", "clc" \ "clpattern", "clp" \
         "clwidth", "clw" \ "color", "col" \ "fcolor", "fc" \
         "fintensity", "fi" \ "bfcolor", "bfc" \ "blcolor", "blc" \
         "acolor", "ac" \ "alcolor", "alc" \ "alwidth", "alw" \
         "alpattern", "alp" \ "mlabel", "ml" \ "jitter", "jitter" \
         "base", "base" \ "barwidth", "barw" \ "pstyle", "psty" \
         "lstyle", "ls" \ "clstyle", "cls" \ "mstyle", "mst" \
         "mlstyle", "mls" \ "astyle", "ast" \ "alstyle", "al" \
         "bstyle", "bst" \ "blstyle", "bl" \ "dstyle", "dst" \
         "dlstyle", "dl" \ "bmlinestyle", "bml" \
         "mlabtextstyle", "mlabt" \ "connect", "c" \ "cmissing", "cmiss")
    for (r = 1; r <= rows(t); r++) {
        if (L >= strlen(t[r, 2]) & L <= strlen(t[r, 1]) &
            substr(t[r, 1], 1, L) == nm) return(t[r, 1])
    }
    return("")
}

// _dash_p_merge(segopts, P, n) -- the plot's option text segopts with the
// p#() values P (one row each: the y it is for, 1 .. n, and its text, in
// the order twoway applies them -- the plot's own, then the graph's)
// applied.  The plot's own options win and, among the p#() values, the
// rightmost (pnum_truth.json prec_own and prec_grp draw blue, twice and
// own_vs_grp the last one).  One y: the values go whole before segopts.
// Several: each stylelist option of a value is one copy K(e1 .. en)
// after segopts, e_i the plot's own element for y_i (from its last copy
// of K), else the last value given for y_i, else "." (multi_own,
// multi_short); any other option of a value is added to the caller's
// local _pm_named as p<j>(<name>), as not drawn.
string scalar _dash_p_merge(string scalar segopts, string matrix P,
                            real scalar n)
{
    string rowvector st, pt, keys
    string matrix    vals
    string scalar    out, named, nm, key, own, e, cp
    real scalar      r, a, b, i, j, kk

    if (n <= 1) {
        out = ""
        for (r = 1; r <= rows(P); r++) out = out + " " + P[r, 2]
        return(strtrim(out + " " + segopts))
    }
    named = st_local("_pm_named")
    keys  = J(1, 0, "")
    vals  = J(0, n, "")
    for (r = 1; r <= rows(P); r++) {
        j  = strtoreal(P[r, 1])
        pt = _dash_opt_tokens(P[r, 2])
        for (a = 1; a <= cols(pt); a++) {
            key = _dash_p_key(pt[a])
            if (key == "") {
                nm = _dash_rep_optname(pt[a])
                if (nm == "") nm = pt[a]
                else if (strpos(pt[a], "(")) nm = nm + "()"
                named = named + " p" + strofreal(j) + "(" + nm + ")"
                continue
            }
            kk = 0
            for (b = 1; b <= cols(keys); b++) if (keys[b] == key) kk = b
            if (!kk) {
                keys = keys, key
                vals = vals \ J(1, n, "")
                kk   = cols(keys)
            }
            vals[kk, j] = _dash_stylelist_pick(_dash_rep_value(pt[a]), 1)
        }
    }
    st_local("_pm_named", strtrim(named))
    out = segopts
    st  = _dash_opt_tokens(segopts)
    for (b = 1; b <= cols(keys); b++) {
        own = ""
        for (a = 1; a <= cols(st); a++) {
            if (_dash_p_key(st[a]) == keys[b]) own = _dash_rep_value(st[a])
        }
        cp = ""
        for (i = 1; i <= n; i++) {
            e = _dash_stylelist_pick(own, i)
            if (e == "") e = vals[b, i]
            if (e == "") e = "."
            else if (strpos(e, char(34))) e = char(96) + char(34) + e + char(34) + char(39)
            else if (strpos(e, " ")) e = char(34) + e + char(34)
            cp = cp + (i > 1 ? " " : "") + e
        }
        out = out + (out == "" ? "" : " ") + keys[b] + "(" + cp + ")"
    }
    return(out)
}

// _dash_p_seg(opts, ptype, n) -- a plot's option text opts with its own
// p<j>() and the graph's p<k>() for it ($dash__pnum, _dash_plot's pairs;
// $dash__poff the plot numbers before this plot) applied
// (_dash_p_merge); n is its number of ys.  A p<j>() past the plot's ys,
// and a graph p<k>() for no y of it, change nothing, silently, as twoway
// draws them (pnum_truth.json plot_n1, plot_over, g_p20).  On a ci fit
// (lfitci qfitci fpfitci lpolyci) a p#() is named in the note as not
// drawn (ci_p1_band).  Sets the caller's locals _pa_named (the p#() words
// not drawn), _pa_nv and _pa_v1 .. (each value applied, for
// _dash_p_apply's check of its options; one at a time, as twoway reads
// each).  p21() and above inside a plot are refused here.  A value's
// marker() is written mstyle(), as twoway reads it there (D62).
string scalar _dash_p_seg(string scalar opts, string scalar ptype,
                          real scalar n)
{
    string matrix    P
    string rowvector toks
    string scalar    rest, gp, named, pr, one
    real scalar      pass, k, c, off, ci, q, hit

    st_local("_pa_named", "")
    st_local("_pa_nv", "0")
    if (n < 1 | n >= .) n = 1
    rest = _dash_p_take(opts)
    if (st_local("_pt_bad") != "") {
        // pnum_truth.json own_p21: (scatter mpg weight, p21(mcolor(red)))
        // is "p21(mcolor(red)):  too many arguments", r(103).
        _dash_say("err", "", st_local("_pt_bad"), ":  too many arguments")
        exit(103)
    }
    gp = st_global("dash__pnum")
    if (st_local("_pt_n") == "0" & gp == "") return(opts)
    ci  = anyof(("lfitci", "qfitci", "fpfitci", "lpolyci"), ptype)
    off = strtoreal(st_global("dash__poff"))
    if (off >= .) off = 0
    P     = J(0, 2, "")
    named = ""
    for (pass = 1; pass <= 2; pass++) {
        pr = (pass == 1 ? st_local("_pt_pairs") : gp)
        while (pr != "") {
            q = strpos(pr, char(1))
            if (q) {
                one = substr(pr, 1, q - 1)
                pr  = substr(pr, q + 1, .)
            }
            else {
                one = pr
                pr  = ""
            }
            c = strpos(one, ":")
            k = strtoreal(substr(one, 1, c - 1)) - (pass == 2 ? off : 0)
            if (k < 1 | k > n) continue
            if (ci) {
                named = named + " p" + strofreal(k + (pass == 2 ? off : 0)) + "()"
                continue
            }
            P = P \ (strofreal(k), substr(one, c + 1, .))
        }
    }
    // D62: inside a p#() value twoway reads marker() as its markerstyle
    // option, mstyle() -- p1(marker(O)) draws mstyle(O)'s picture with its
    // note, p1(marker(p3)) mstyle(p3)'s (dash_only_words_truth.json
    // p.marker, pmarker.*) -- so the word is written as mstyle() here.
    for (k = 1; k <= rows(P); k++) {
        toks = _dash_rep_toks(P[k, 2], 0)
        hit  = 0
        for (c = 1; c <= cols(toks); c++) {
            if (_dash_rep_optname(toks[c]) == "marker" &
                substr(toks[c], 1, 7) == "marker(") {
                toks[c] = "mstyle" + substr(toks[c], 7, .)
                hit = 1
            }
        }
        if (hit) P[k, 2] = invtokens(toks, " ")
    }
    for (k = 1; k <= rows(P); k++) st_local("_pa_v" + strofreal(k), P[k, 2])
    for (k = 1; k <= rows(P); k++) st_local("_pa_k" + strofreal(k), P[k, 1])
    st_local("_pa_nv", strofreal(rows(P)))
    st_local("_pm_named", "")
    if (rows(P)) rest = _dash_p_merge(rest, P, n)
    st_local("_pa_named", strtrim(named + " " + st_local("_pm_named")))
    return(rest)
}

// _dash_p_unknown(unk, ptype) -- refuses the options of the p#() values
// that twoway does not take on ptype (unk: what _dash_parse_plot_opts's
// catch-all kept of them) as twoway refuses them, all named as typed:
// pnum_truth.json bad_inner, p1(nosuch(1)) is "option(s) nosuch(1) not
// allowed", r(198).
void _dash_p_unknown(string scalar unk, string scalar ptype)
{
    string rowvector u
    string scalar    bad
    real scalar      i

    u   = _dash_rep_toks(unk, 0)
    bad = ""
    for (i = 1; i <= cols(u); i++) {
        if (_dash_tw_takes(u[i], ptype, 0)) continue
        bad = bad + (bad == "" ? "" : " ") + u[i]
    }
    if (bad == "") return
    _dash_say("err", "option(s) ", substr(bad, 1, 80), " not allowed")
    exit(198)
}

// ============================================================
// The spellings dash took and twoway refuses (WP-35 DT-15).  The
// maintainer ruled (DECISIONS.md P4-7, D53): unless an option is specific
// to what only dash does (hover(), table), its syntax mirrors twoway's, so
// each spelling below is refused as twoway refuses it, "option <word>()
// not allowed", r(198), and a second line names twoway's spelling (P4-9).
// Measured 27oct2026, test/fixtures/dash_only_words_truth.json
// (scripts/extract_dash_only_truth.do); the words are pinned to
// test/dash_only_rulings.py by test/test_dash_only_words.py.

// _dash_dashonly_list() -- one row per refused word: its full name, dash's
// minimum spelling (the capitals of its declaration), "1" when it takes a
// value, the hint line, and "1" when twoway refuses it inside a p<k>()
// text too ("0": twoway takes marker() there as its markerstyle option,
// the fixture's p.marker).  The declarations and folds stay:
// _dash_route_axis2 writes ytitle2() .. for ytitle(..., axis(2)).
string matrix _dash_dashonly_list()
{
    return(("ytitle2", "ytitle2", "1", "use ytitle(..., axis(2))", "1" \
            "ylabel2", "ylabel2", "1", "use ylabel(..., axis(2))", "1" \
            "yscale2", "yscale2", "1", "use yscale(..., axis(2))", "1" \
            "xtitle2", "xtitle2", "1", "use xtitle(..., axis(2))", "1" \
            "xlabel2", "xlabel2", "1", "use xlabel(..., axis(2))", "1" \
            "xscale2", "xscale2", "1", "use xscale(..., axis(2))", "1" \
            "yti2", "yti2", "1", "use ytitle(..., axis(2))", "1" \
            "yla2", "yla2", "1", "use ylabel(..., axis(2))", "1" \
            "ysc2", "ysc2", "1", "use yscale(..., axis(2))", "1" \
            "xti2", "xti2", "1", "use xtitle(..., axis(2))", "1" \
            "xla2", "xla2", "1", "use xlabel(..., axis(2))", "1" \
            "xsc2", "xsc2", "1", "use xscale(..., axis(2))", "1" \
            "ytick2", "ytick2", "1", "use ytick(..., axis(2))", "1" \
            "xtick2", "xtick2", "1", "use xtick(..., axis(2))", "1" \
            "yline2", "yline2", "1", "use yline(..., axis(2))", "1" \
            "xline2", "xline2", "1", "use xline(..., axis(2))", "1" \
            "ymtick2", "ymtick2", "1", "use ymtick(..., axis(2))", "1" \
            "ymlabel2", "ymlabel2", "1", "use ymlabel(..., axis(2))", "1" \
            "xmtick2", "xmtick2", "1", "use xmtick(..., axis(2))", "1" \
            "xmlabel2", "xmlabel2", "1", "use xmlabel(..., axis(2))", "1" \
            "tlabel2", "tlabel2", "1", "use tlabel(..., axis(2))", "1" \
            "ttick2", "ttick2", "1", "use ttick(..., axis(2))", "1" \
            "tline2", "tline2", "1", "use tline(..., axis(2))", "1" \
            "tscale2", "tscale2", "1", "use tscale(..., axis(2))", "1" \
            "ttitle2", "ttitle2", "1", "use ttitle(..., axis(2))", "1" \
            "marker", "marker", "1", "use msymbol()", "0" \
            "malpha", "mal", "1", "use mcolor(<color>%<#>)", "1" \
            "lalpha", "lalp", "1", "use lcolor(<color>%<#>)", "1" \
            "falpha", "fa", "1", "use fcolor(<color>%<#>)", "1" \
            "jseed", "jse", "1", "use jitterseed()", "1" \
            "mlg", "mlg", "1", "use mlabgap()", "1" \
            "cv", "cv", "1", "use colorvar()", "1" \
            "colv", "colv", "1", "use colorvar()", "1" \
            "colornlevels", "colorn", "1", "use colorlevels()", "1" \
            "colormissing", "colorm", "1", "use colorformissing()", "1" \
            "plotbgcolor", "plotbgcolor", "1", "use plotregion(fcolor())", "1" \
            "pbgc", "pbgc", "1", "use plotregion(fcolor())", "1" \
            "colpalette", "colpal", "1", "use colorlist() or colorrule()", "1"))
}

// _dash_dashonly_typed(text, inp) -- the first word of the option text
// text, as typed, that is a spelling of _dash_dashonly_list() (from its
// minimum to its full name, lower case as twoway reads it), or "" for
// none.  Read by value.  Counted are the option words (_dash_rep_optname
// non-empty) other than p<k>() (taken out before the parse, so the count
// is the same with or without them).  inp 1: text is a p<k>() text, and
// the rows twoway takes there are skipped.  Returns "<row>|<index>|<hint>|
// <name as twoway names it>|<word as typed>", <index> the hit's place
// among the counted words, the word cut to 80 characters; sets the
// caller's locals _do_pre (the counted words before the hit, one blank
// between them) and _do_all (every hit word, cut to 80 characters, in
// typed order, one blank between them; with inp 1 each written as
// twoway's p# line writes it: a blank inside its parentheses between two
// characters other than "(" and ")" doubled, the fixture's p.ylabel2 and
// space.run).
string scalar _dash_dashonly_typed(string scalar text, real scalar inp)
{
    string matrix    t
    string rowvector toks
    string scalar    nm, first, pre, all, w
    real scalar      i, r, k, L, hit

    st_local("_do_pre", "")
    st_local("_do_all", "")
    if (strtrim(text) == "") return("")
    t     = _dash_dashonly_list()
    toks  = _dash_rep_toks(text, 0)
    first = ""
    pre   = ""
    all   = ""
    k     = 0
    for (i = 1; i <= cols(toks); i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        if (ustrregexm(toks[i], "^p[1-9][0-9]*\(")) continue
        k++
        L   = strlen(nm)
        hit = 0
        for (r = 1; r <= rows(t); r++) {
            if (inp & t[r, 5] == "0") continue
            if (L >= strlen(t[r, 2]) & L <= strlen(t[r, 1]) &
                substr(t[r, 1], 1, L) == nm) {
                hit = r
                break
            }
        }
        if (!hit) {
            if (first == "") pre = pre + (pre == "" ? "" : " ") + toks[i]
            continue
        }
        w = (inp ? _dash_dashonly_blanks(toks[i]) : toks[i])
        all = all + (all == "" ? "" : " ") + substr(w, 1, 80)
        if (first != "") continue
        first = strofreal(hit) + "|" + strofreal(k) + "|" + t[hit, 4] + "|" +
                nm + (strpos(toks[i], "(") ? "()" : "") + "|" +
                substr(toks[i], 1, 80)
    }
    st_local("_do_pre", pre)
    st_local("_do_all", all)
    return(first)
}

// _dash_dashonly_say(hit, toks) -- refuses the hit _dash_dashonly_typed
// returned, r(198): twoway's line, "option <name> not allowed", or with
// toks (the p#() words, as twoway lists them) "option(s) <toks> not
// allowed", then the hint line naming twoway's spelling (P4-9), and
// nothing else.
void _dash_dashonly_say(string scalar hit, string scalar toks)
{
    string rowvector f
    string scalar    rest
    real scalar      i, q

    f    = J(1, 4, "")
    rest = hit
    for (i = 1; i <= 4; i++) {
        q = strpos(rest, "|")
        if (!q) break
        f[i] = substr(rest, 1, q - 1)
        rest = substr(rest, q + 1, .)
    }
    if (toks != "") _dash_say("err", "option(s) ", toks, " not allowed")
    else _dash_say("err", "option ", f[4], " not allowed")
    if (f[3] != "") _dash_say("err", "      ", f[3], "")
    exit(198)
}

// _dash_dashonly_blanks(w) -- the option word w as twoway's p# line
// writes it: each run of blanks inside its parentheses that lies between
// two characters other than "(" and ")" gains one blank (measured
// 27oct2026: ylabel2(10 20) is written ylabel2(10  20), ytitle2(a   b)
// ytitle2(a    b), mlg( 2 ) as typed; dash_only_words_truth.json).
string scalar _dash_dashonly_blanks(string scalar w)
{
    string scalar out, c, prev
    real scalar   i, j, n, p

    p = strpos(w, "(")
    if (!p) return(w)
    n    = strlen(w)
    out  = substr(w, 1, p)
    prev = "("
    i    = p + 1
    while (i <= n) {
        c = substr(w, i, 1)
        if (c != " ") {
            out  = out + c
            prev = c
            i++
            continue
        }
        j = i
        while (j <= n & substr(w, j, 1) == " ") j++
        out = out + substr(w, i, j - i)
        if (prev != "(" & prev != ")" & j <= n & substr(w, j, 1) != ")" &
            substr(w, j, 1) != "(") out = out + " "
        i = j
    }
    return(out)
}

// _dash_tw_silent_tab() -- the options dash names in its note as not
// drawn that twoway takes and draws nothing different with (WP-32, BUGS.md
// "dash names options twoway takes and draws nothing of, where twoway is
// silent"): one row each, its name and the plot types where its picture
// is twoway's without it (measured 19oct2026, graph export SVG,
// test/fixtures/noted_option_truth.json).  dash takes each there without
// a note, as twoway does.
string matrix _dash_tw_silent_tab()
{
    string matrix t

    t = J(0, 2, "")
    // BEGIN tw_silent (generated by scripts/gen_twoway_takes_table.py from test/fixtures/noted_option_truth.json; do not edit)
    t = t \ ("acolor", "scatter line connected dot tsline rscatter contour contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("alcolor", "scatter line connected dot tsline rscatter contour contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("alpattern", "scatter line connected dot tsline rscatter contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("alstyle", "scatter line connected dot tsline rscatter contour contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("alwidth", "scatter line connected dot tsline rscatter contour contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("barbsize", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike contour contourline pcspike pccapsym pcscatter pci scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("baroffset", "area spike dropline dot")
    t = t \ ("blstyle", "scatter line connected dot tsline rscatter contour contourline pcscatter scatteri lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("bmlinestyle", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike contour contourline pcspike pccapsym pcarrow pcbarrow pcscatter pci pcarrowi scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("headlabel", "rpcap rpspike pcspike pci")
    t = t \ ("lstyle", "scatter dot rscatter contour contourline pcscatter scatteri")
    t = t \ ("mangle", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike contour contourline pcspike pccapsym pcscatter pci scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("mlstyle", "line area bar spike tsline tsrline rarea rbar rspike rcap rline contour contourline pcspike pci lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("msize", "scatter line connected area bar spike dropline dot tsline tsrline rarea rbar rspike rcap rline rconnected rcapsym rscatter rpcap rpspike contour contourline pcspike pccapsym pcscatter pci scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("mstyle", "line area bar spike tsline tsrline rarea rbar rspike rcap rline contour contourline pcspike pci lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    t = t \ ("outlines", "contourline")
    t = t \ ("recast", "line dot tsline rpspike contour pcspike pci lfit qfit fpfit lowess lpoly mspline mband kdensity function")
    t = t \ ("sort", "tsline tsrline contourline pci pcarrowi scatteri lfit qfit lfitci qfitci fpfit fpfitci lowess lpoly lpolyci mspline mband kdensity histogram function")
    // END tw_silent
    return(t)
}

// _dash_silent_drop(p, ptype) -- the pending names p (s(_pending)) less
// those twoway draws nothing different with on plot type ptype
// (_dash_tw_silent_tab), one blank between them.
string scalar _dash_silent_drop(string scalar p, string scalar ptype)
{
    string matrix    t
    string rowvector w
    string scalar    out
    real scalar      i, r, drop

    t = _dash_tw_silent_tab()
    w = tokens(p)
    out = ""
    for (i = 1; i <= cols(w); i++) {
        drop = 0
        for (r = 1; r <= rows(t); r++) {
            if (t[r, 1] == w[i] & anyof(tokens(t[r, 2]), ptype)) drop = 1
        }
        if (!drop) out = out + (out == "" ? "" : " ") + w[i]
    }
    return(out)
}

// _dash_tw_value_tab() -- twoway's return code and first line for each
// option value it refuses (WP-35 basic:PT-9): one row per option, the
// plot types it holds on ("*" for every type, else type|type), the class
// of the failing value as _dash_validate_value computes it (missing, nan,
// huge, inf, nonint, below, above, dots), the rc and the line, %v standing
// for the value as typed.  Measured: test/fixtures/value_truth.json and
// test/fixtures/value_codes_truth.json.  Read by _dash_tw_value_msg only.
string matrix _dash_tw_value_tab()
{
    string matrix t

    // BEGIN tw_value (generated by scripts/gen_value_refusal_table.py from test/fixtures/value_truth.json and test/fixtures/value_codes_truth.json; do not edit)
    t = J(0, 5, "")
    t = t \ ("alwidth", "area|bar|dropline|fpfitci|histogram|lfitci|lpolyci|pcarrow|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rspike|spike|tsrline", "above", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("alwidth", "area|bar|dropline|fpfitci|histogram|lfitci|lpolyci|pcarrow|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rspike|spike|tsrline", "below", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("aspectratio", "*", "nan", "198", "option aspectratio() incorrectly specified")
    t = t \ ("bands", "*", "above", "198", "bands must be between 1 and 200")
    t = t \ ("bands", "*", "below", "198", "bands must be between 1 and 200")
    t = t \ ("bands", "*", "nan", "198", "option bands() not allowed")
    t = t \ ("bands", "*", "nonint", "198", "option bands() not allowed")
    t = t \ ("barwidth", "*", "missing", "199", "unrecognized command")
    t = t \ ("barwidth", "*", "nan", "198", "option barwidth() incorrectly specified")
    t = t \ ("base", "*", "nan", "4026", "option base() incorrectly specified, %v is not a number")
    t = t \ ("bin", "*", "below", "125", "bins() invalid -- invalid number, outside of allowed range")
    t = t \ ("bin", "*", "nan", "121", "bins() invalid -- invalid number")
    t = t \ ("bin", "*", "nonint", "126", "bins() invalid -- invalid number, noninteger value")
    t = t \ ("bwidth", "area|bar|connected|contour|contourline|dot|dropline|fpfit|fpfitci|function|histogram|lfit|lfitci|line|lpoly|lpolyci|mband|mspline|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfit|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rscatter|rspike|scatter|scatteri|spike|tsline|tsrline", "below", "198", "bwidth() must be a positive number")
    t = t \ ("bwidth", "kdensity", "below", "198", "bandwidth must be positive")
    t = t \ ("bwidth", "area|bar|connected|contour|contourline|dot|dropline|fpfit|fpfitci|function|histogram|lfit|lfitci|line|lpoly|lpolyci|mband|mspline|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfit|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rscatter|rspike|scatter|scatteri|spike|tsline|tsrline", "nan", "111", "variable %v not found")
    t = t \ ("bwidth", "kdensity", "nan", "198", "option bwidth() not allowed")
    t = t \ ("bwidth", "lowess", "nan", "198", "option bwidth() not allowed")
    t = t \ ("clwidth", "area|bar|connected|contour|contourline|dot|dropline|fpfit|fpfitci|function|histogram|kdensity|lfit|lfitci|line|lowess|lpoly|lpolyci|mband|mspline|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfit|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rscatter|rspike|scatteri|spike|tsline|tsrline", "below", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("colorlevels", "*", "nan", "198", "option colorlevels() incorrectly specified")
    t = t \ ("colorlevels", "*", "nonint", "198", "option colorlevels() incorrectly specified")
    t = t \ ("degree", "*", "below", "198", "degree() must be a nonnegative number")
    t = t \ ("degree", "*", "nan", "198", "option degree() not allowed")
    t = t \ ("degree", "*", "nonint", "198", "option degree() not allowed")
    t = t \ ("jitter", "*", "huge", "198", ".z_ invalid name")
    t = t \ ("kernel", "*", "nan", "198", "invalid kernel function")
    t = t \ ("level", "fpfitci|lfitci|qfitci", "nan", "198", "option level() not allowed")
    t = t \ ("lwidth", "area|bar|connected|contour|dropline|fpfit|fpfitci|function|histogram|kdensity|lfit|lfitci|line|lowess|lpoly|lpolyci|mband|mspline|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|qfit|qfitci|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rspike|spike|tsline|tsrline", "below", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("mlabangle", "bar|connected|dot|dropline|pccapsym|pcscatter|rcapsym|rconnected|rscatter|scatter|scatteri", "above", "198", "textangle must be between -360.000 and 360.000")
    t = t \ ("mlabangle", "bar|connected|dot|dropline|pccapsym|pcscatter|rcapsym|rconnected|rscatter|scatter|scatteri", "huge", "111", "variable z_ not found")
    t = t \ ("mlabel", "*", "dots", "101", "factor-variable and time-series operators not allowed")
    t = t \ ("mlwidth", "connected|contour|dot|dropline|pcarrow|pcarrowi|pcbarrow|pccapsym|pcscatter|rcapsym|rconnected|rpcap|rpspike|rscatter|scatter|scatteri", "below", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("msangle", "connected|dot|dropline|pcarrow|pcarrowi|pcbarrow|pccapsym|pcscatter|rcapsym|rconnected|rpcap|rpspike|rscatter|scatter|scatteri", "above", "198", "symbolangle must be between -360.000 and 360.000")
    t = t \ ("msangle", "contour", "above", "198", "gm_linewidth must be between 0.000 and 1.0e+04")
    t = t \ ("msangle", "connected|contour|dot|dropline|pcarrow|pcarrowi|pcbarrow|pccapsym|pcscatter|rcapsym|rconnected|rpcap|rpspike|rscatter|scatter|scatteri", "huge", "198", ".z_ invalid name")
    t = t \ ("msize", "*", "huge", "198", "invalid syntax")
    t = t \ ("n", "mspline", "above", "198", "n must be between 1 and 300")
    t = t \ ("n", "kdensity", "below", "198", "option n() requires a positive integer")
    t = t \ ("n", "lpoly", "below", "198", "n() must be a positive number")
    t = t \ ("n", "mspline", "below", "198", "n must be between 1 and 300")
    t = t \ ("n", "area|bar|connected|contour|contourline|dot|dropline|fpfit|function|histogram|kdensity|line|lowess|lpoly|lpolyci|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rscatter|rspike|scatter|scatteri|spike|tsline|tsrline", "nan", "198", "option n() not allowed")
    t = t \ ("n", "lfit|lfitci|qfit|qfitci", "nan", "198", "option n() not allowed")
    t = t \ ("n", "mband", "nan", "198", "option n() not allowed")
    t = t \ ("n", "mspline", "nan", "198", "option n() not allowed")
    t = t \ ("n", "area|bar|connected|contour|contourline|dot|dropline|fpfit|function|histogram|kdensity|line|lowess|lpoly|lpolyci|pcarrow|pcarrowi|pcbarrow|pccapsym|pci|pcscatter|pcspike|rarea|rbar|rcap|rcapsym|rconnected|rline|rpcap|rpspike|rscatter|rspike|scatter|scatteri|spike|tsline|tsrline", "nonint", "198", "option n() not allowed")
    t = t \ ("n", "lfit|lfitci|qfit|qfitci", "nonint", "198", "option n() not allowed")
    t = t \ ("n", "mband", "nonint", "198", "option n() not allowed")
    t = t \ ("n", "mspline", "nonint", "198", "option n() not allowed")
    t = t \ ("start", "*", "nan", "121", "start() invalid -- invalid number")
    t = t \ ("width", "*", "below", "125", "width() invalid -- invalid number, outside of allowed range")
    t = t \ ("width", "*", "nan", "121", "width() invalid -- invalid number")
    // END tw_value
    return(t)
}

// _dash_tw_value_msg(opt, ptype, cls, value) -- "<rc>|<line>" for the row
// of _dash_tw_value_tab that holds option opt on plot type ptype ("" for a
// graph option: a "*" row only) for a value of class cls, the line's %v
// replaced by the value as typed (cut to 80 characters); "" when twoway's
// refusal of it is not measured.  A row naming ptype wins over a "*" row.
// The caller prints the line through _dash_say.
string scalar _dash_tw_value_msg(string scalar opt, string scalar ptype,
                                 string scalar cls, string scalar value)
{
    string matrix t
    real scalar   r, hit

    t = _dash_tw_value_tab()
    hit = 0
    for (r = 1; r <= rows(t); r++) {
        if (t[r, 1] != opt | t[r, 3] != cls) continue
        if (t[r, 2] == "*") {
            if (!hit) hit = r
        }
        else if (ptype != "" & anyof(tokens(subinstr(t[r, 2], "|", " ")), ptype)) {
            hit = r
            break
        }
    }
    if (!hit) return("")
    return(t[hit, 4] + "|" + subinstr(t[hit, 5], "%v", usubstr(value, 1, 80)))
}

// _dash_tw_refuses(tok, ptype, graph) -- 1 when the option word tok is a
// spelling of a row of _dash_tw_refuses_tab that twoway refuses on plot
// type ptype (graph 1: after the plot groups' comma), with a value or
// without: twoway refuses both forms, naming the word as typed; or a bare
// replace, which twoway refuses everywhere.
real scalar _dash_tw_refuses(string scalar tok, string scalar ptype,
                             real scalar graph)
{
    string matrix t
    string scalar nm
    real scalar   r, L

    nm = _dash_rep_optname(tok)
    if (nm == "") return(0)
    // A bare replace: twoway refuses it in every position, "option replace
    // not allowed", r(198) (noted_option_truth.json graph_level), beside
    // saving() too; saving(f, replace) is its replace.
    if (nm == "replace" & !strpos(tok, "(")) return(1)
    L = strlen(nm)
    t = _dash_tw_refuses_tab()
    for (r = 1; r <= rows(t); r++) {
        if (L < strlen(t[r, 2]) | L > strlen(t[r, 1])) continue
        if (substr(t[r, 1], 1, L) != nm) continue
        if (graph) return(t[r, 4] == "1")
        return(t[r, 3] == "*" | anyof(tokens(t[r, 3]), ptype))
    }
    return(0)
}

// _dash_unknown_scan(opts, unk, ptype, graph) -- the option words of a
// list, in order, for dash.ado's _dash_refuse_unknown (WP-32): twoway
// names the first word of a list it does not take, "option bogus not
// allowed", r(198), whatever follows it (measured 19oct2026,
// test/fixtures/unknown_option_truth.json orders).  Sets the caller's
// local _uk_n (at most 300 words) and, for each, _uk_tok<i> (the word),
// _uk_nm<i> (its name as typed, "()" after it when it took a value) and
// _uk_cls<i>: "uc" for a name not in lower case, "jit" for a spelling of
// jitter() short of twoway's minimum, "short" for one of name() or
// aspectratio() short of it, or title2() or subtitle2(), which twoway has
// not, or an option dash declares that twoway refuses here
// (_dash_tw_refuses); "cand" for a word the parser's catch-all (unk) holds by name that
// twoway does not take here (_dash_tw_takes), which the caller puts to the
// parser alone; "" otherwise.  _uk_go is 1 when some word is classed.
// Read by value; the words are the user's.
void _dash_unknown_scan(string scalar opts, string scalar unk,
                        string scalar ptype, real scalar graph)
{
    string rowvector toks, u, unames
    string scalar    nm, si, cls
    real scalar      i, n, go

    u = _dash_rep_toks(unk, 0)
    unames = J(1, cols(u), "")
    for (i = 1; i <= cols(u); i++) unames[i] = _dash_rep_optname(u[i])
    toks = _dash_rep_toks(opts, 0)
    n  = 0
    go = 0
    for (i = 1; i <= cols(toks) & n < 300; i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        n++
        si = strofreal(n)
        cls = ""
        if (nm != strlower(nm)) cls = "uc"
        else if (anyof(("j", "ji", "jit", "jitt", "jitte"), nm)) cls = "jit"
        else if (anyof(("na", "nam", "asp", "aspe", "aspec", "title2",
                        "subtitle2"), nm)) cls = "short"
        else if (_dash_tw_refuses(toks[i], ptype, graph)) cls = "short"
        else if (anyof(unames, nm) & !_dash_tw_takes(toks[i], ptype, graph))
            cls = "cand"
        if (cls != "") go = 1
        st_local("_uk_tok" + si, toks[i])
        st_local("_uk_nm" + si, nm + (strpos(toks[i], "(") ? "()" : ""))
        st_local("_uk_cls" + si, cls)
    }
    st_local("_uk_n", strofreal(n))
    st_local("_uk_go", strofreal(go))
}

// _dash_rep_prefix(opts, n) -- the first n option words of opts, as
// typed, one blank between them (_dash_refuse_unknown).
string scalar _dash_rep_prefix(string scalar opts, real scalar n)
{
    string rowvector toks
    string scalar    out
    real scalar      i, k

    toks = _dash_rep_toks(opts, 0)
    out = ""
    k = 0
    for (i = 1; i <= cols(toks) & k < n; i++) {
        if (_dash_rep_optname(toks[i]) == "") continue
        out = out + (out == "" ? "" : " ") + toks[i]
        k++
    }
    return(out)
}

// _dash_opt_typed(opts, canon, table) -- the option word of opts that the
// option canon names, as typed, for a refusal's first line: twoway names
// the option as it was typed ("option ba() not allowed" for ba(3) where
// bands() is meant; WP-49 plot:PT-7, test/fixtures/refusal_line_truth.json
// pt7.typed.*).  canon is the name as the refusal prints it: "bands()" for
// an option that takes a value, "atobs" for one that takes none.  The
// first word of opts (read by _dash_rep_toks and _dash_rep_optname) whose
// name abbreviates canon's -- for table "plot" or "graph" a leading part
// of the name, for a sub-option family (_dash_so_canon's table) the
// family's own minimum -- and that takes a value exactly when canon does
// (so n(5) is never read as nofit) is returned with "()" when it takes
// one, its name cut to 32 characters as Stata names are; canon itself
// when no word is (an option given in p#() or written by dash).
string scalar _dash_opt_typed(string scalar opts, string scalar canon,
                              string scalar table)
{
    string rowvector w
    string scalar    nm, full
    real scalar      i, val

    val  = (substr(canon, -2, 2) == "()")
    full = (val ? substr(canon, 1, strlen(canon) - 2) : canon)
    if (full == "") return(canon)
    w = _dash_rep_toks(opts, 1)
    for (i = 1; i <= cols(w); i++) {
        nm = _dash_rep_optname(w[i])
        if (nm == "" | (strpos(w[i], "(") > 0) != val) continue
        if (table == "plot" | table == "graph") {
            if (strlen(nm) > strlen(full) | substr(full, 1, strlen(nm)) != nm) continue
        }
        else if (_dash_so_canon(nm, table) != full) continue
        return(substr(nm, 1, 32) + (val ? "()" : ""))
    }
    return(canon)
}

// _dash_pending_note(p) -- the pending names p (s(_pending): options dash
// declares and does not draw, bare names) as the note writes them: "()"
// after each that takes a value, none after outlines, mwidth and
// headlabel, which take none, and none after sort unless sort(varlist) was
// given (s(sort1), the plot parser's), as twoway names a word as typed
// (WP-32).
string scalar _dash_pending_note(string scalar p)
{
    string rowvector w
    string scalar    out
    real scalar      i

    w = tokens(p)
    out = ""
    for (i = 1; i <= cols(w); i++) {
        // headlabel takes no value, and sort is named as typed: sort()
        // when sort(varlist) was given (s(sort1)), else sort (WP-32).
        out = out + " " + w[i] +
              (anyof(("outlines", "mwidth", "headlabel"), w[i]) |
               (w[i] == "sort" & strtrim(st_global("s(sort1)")) == "") ?
               "" : "()")
    }
    return(strtrim(out))
}

// _dash_valued_names(raw) -- the option names of raw typed with a value,
// one blank between them (WP-32: _dash_report_ignored writes "()" after
// these alone).  Read by value; the words are the user's.
string scalar _dash_valued_names(string scalar raw)
{
    string rowvector toks
    string scalar    out, nm
    real scalar      i

    toks = _dash_rep_toks(raw, 0)
    out = ""
    for (i = 1; i <= cols(toks); i++) {
        if (!strpos(toks[i], "(")) continue
        nm = _dash_rep_optname(toks[i])
        if (nm != "") out = out + " " + nm
    }
    return(strtrim(out))
}

// _dash_kernel_clash(opts, ptype) -- how twoway answers two kernels in
// one option list of lpoly, lpolyci or kdensity: "old" when a kernel
// written as an option of its own (gaussian, ep, epan2 ...) stands beside
// kernel() -- "kernel(): old syntax may not be combined with new syntax",
// whatever kernel() holds -- "one" when two such options name different
// kernels -- "only one kernel may be specified" (ep and epan2 are two) --
// and "" otherwise, or on any other type.  Measured 24sep2026, r(198) for
// each, after twoway's refusal of a repeated option (gaussian gaussian,
// kernel() twice).  kernel() is any spelling k( .. kernel(, as twoway
// abbreviates it; a flag is a row of _dash_rep_und_tab.
string scalar _dash_kernel_clash(string scalar opts, string scalar ptype)
{
    string matrix    tab
    string rowvector toks, seen
    string scalar    nm
    real colvector   ok
    real scalar      i, r, kfun

    if (!anyof(("lpoly", "lpolyci", "kdensity"), ptype)) return("")
    tab  = _dash_rep_und_tab()
    ok   = _dash_rep_und_rows(tab, ptype)
    toks = _dash_rep_toks(opts, 0)
    seen = J(1, 0, "")
    kfun = 0
    for (i = 1; i <= cols(toks); i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        if (strpos(toks[i], "(") & strlen(nm) <= 6 &
            substr("kernel", 1, strlen(nm)) == nm) {
            kfun = 1
            continue
        }
        r = _dash_rep_und_row(toks[i], tab, ok)
        if (!r) continue
        if (!anyof(("epanechnikov", "epan2", "biweight", "cosine",
                    "gaussian", "parzen", "rectangle", "triangle"),
                   tab[r, 1])) continue
        if (!anyof(seen, tab[r, 1])) seen = seen, tab[r, 1]
    }
    if (cols(seen) & kfun) return("old")
    if (cols(seen) > 1) return("one")
    return("")
}

// _dash_zyx_abbrev(unk, raw) -- contour's and contourline's spellings
// twoway reads and the plot parser leaves to its catch-all unk (WP-35
// stat:PT-13; twoway_zyx2view_parse.class Interp and COLORLines): i() ..
// inter() are interp() (interp() itself is _dash_contour_split's), and a
// bare colorl .. colorline is colorlines (measured 26oct2026,
// test/fixtures/stat_accept_truth.json contour.*).  Sets the caller's
// locals _za_iset (1 when an interp() spelling is in unk), _za_interp (the
// value of the rightmost interp() spelling of the option text raw, in
// order, twoway's _parse combop ... rightmost), _za_cl (1 for a colorlines
// spelling) and _za_rest (unk less those words).  Read by value; the words
// are the user's.
void _dash_zyx_abbrev(string scalar unk, string scalar raw)
{
    string rowvector u, t
    string scalar    nm, rest, v
    real scalar      i, ab, cl, p

    st_local("_za_iset", "0")
    st_local("_za_cl", "0")
    st_local("_za_interp", "")
    st_local("_za_rest", unk)
    u = _dash_opt_tokens(unk)
    rest = ""
    ab = 0
    cl = 0
    for (i = 1; i <= cols(u); i++) {
        nm = _dash_rep_optname(u[i])
        if (anyof(("i", "in", "int", "inte", "inter"), nm) & strpos(u[i], "(")) {
            ab = 1
            continue
        }
        if (anyof(("colorl", "colorli", "colorlin", "colorline"), nm) &
            !strpos(u[i], "(")) {
            cl = 1
            continue
        }
        rest = rest + (rest == "" ? "" : " ") + u[i]
    }
    if (!ab & !cl) return
    st_local("_za_rest", rest)
    st_local("_za_cl", strofreal(cl))
    if (!ab) return
    t = _dash_opt_tokens(raw)
    v = ""
    for (i = 1; i <= cols(t); i++) {
        nm = _dash_rep_optname(t[i])
        p = strpos(t[i], "(")
        if (p & anyof(("i", "in", "int", "inte", "inter", "interp"), nm)) {
            v = substr(t[i], p + 1, strlen(t[i]) - p - 1)
        }
    }
    st_local("_za_iset", "1")
    st_local("_za_interp", v)
}

// _dash_kernel_flag(unk, ptype) -- a kernel written as an option of its
// own, twoway's old syntax, read as kernel(<name>): on lpoly, lpolyci and
// kdensity, the first word of the catch-all unk that is a kernel row of
// _dash_rep_und_tab (bi .. biweight, cos .. cosine, ep .. epanechnikov,
// epan2, gau .. gaussian, par .. parzen, rec .. rectangle, tri ..
// triangle, lower case, with no value).  Sets the caller's local _kf_name
// to the full name, "" when there is none or on any other type, and
// _kf_rest to unk less every such word.  Measured 24sep2026: each spelling
// on each of the three types draws the serset of kernel(<name>); a shorter
// one (e, b, co, ga, pa, re, tr) and every spelling on another type are
// "option ... not allowed", r(198).  Called after _dash_kernel_clash and
// the repeat checks, so at most one kernel is left.  Linear in the words
// of unk; the words are the user's text, read by value.
void _dash_kernel_flag(string scalar unk, string scalar ptype)
{
    string matrix    tab
    string rowvector toks
    string scalar    name, rest
    real colvector   ok
    real scalar      i, r

    st_local("_kf_name", "")
    st_local("_kf_rest", unk)
    if (!anyof(("lpoly", "lpolyci", "kdensity"), ptype)) return
    tab  = _dash_rep_und_tab()
    ok   = _dash_rep_und_rows(tab, ptype)
    toks = _dash_rep_toks(unk, 0)
    name = ""
    rest = ""
    for (i = 1; i <= cols(toks); i++) {
        r = _dash_rep_und_row(toks[i], tab, ok)
        if (r) {
            if (anyof(("epanechnikov", "epan2", "biweight", "cosine",
                       "gaussian", "parzen", "rectangle", "triangle"),
                      tab[r, 1])) {
                if (name == "") name = tab[r, 1]
                continue
            }
        }
        rest = rest + (rest == "" ? "" : " ") + toks[i]
    }
    if (name == "") return
    st_local("_kf_name", name)
    st_local("_kf_rest", rest)
}

// _dash_lpolyci_opts(unk, ptype) -- lpolyci's pwidth(#) and var(#) (WP-29
// P0.9), read from the catch-all unk by value, and the checks twoway makes
// on them and on level(), in twoway's order (measured 01oct2026, StataNow
// 19.5, `twoway lpolyci mpg weight, <opts> nodraw'):
//   1. var() not one number: r(7) "'<tok>' found where number expected",
//      or "'<2nd tok>' found where nothing expected";
//   2. level() not one number (s(level)): r(7), the same words;
//   then, only when every degree() and n() typed is an integer (else
//   twoway's syntax refuses that option first, and so does dash's table):
//   3. level() with an exponent: r(198) "<text> found where number
//      expected"; outside 10..99.99: r(198) "level() must be between 10
//      and 99.99 inclusive"; more than two digits after the point as
//      typed: r(198) "level() can have at most two digits after the
//      decimal point";
//   4. pwidth() not a positive number: r(198) "pwidth() must be a
//      positive number".
// var() <= 0 is refused later, after the kernel, bwidth and degree rules
// (_dash_validate_opts), as twoway orders it.  On ptype "lpolyci" only, a
// word pw..pwidth(...) (minimum pw: p() is twoway's own p() option) or v..var(...)
// (minimum v) is taken out of unk; every other word stays.  Sets the
// caller's locals _lpo_pwidth and _lpo_var (the value, %21.0g), _lpo_rest
// (unk less those words), _lpo_rc (0 or the return code) and _lpo_msg.
// A value is a number when it is one token and strtoreal() is not
// missing.  Nothing is expanded; the words are the user's text.
real scalar _dash_lpo_onenum(string scalar v, real scalar x,
                             string scalar msg)
{
    string rowvector t

    t = tokens(strtrim(v))
    x = .
    if (cols(t) == 0) {
        msg = "'' found where number expected"
        return(0)
    }
    if (cols(t) > 1) {
        x = strtoreal(t[1])
        if (x >= .) {
            msg = "'" + t[1] + "' found where number expected"
            return(0)
        }
        msg = "'" + t[2] + "' found where nothing expected"
        return(0)
    }
    x = strtoreal(t[1])
    if (x >= .) {
        msg = "'" + t[1] + "' found where number expected"
        return(0)
    }
    return(1)
}

real scalar _dash_lpo_isint(string scalar v)
{
    real scalar x

    if (strtrim(v) == "") return(1)
    x = strtoreal(strtrim(v))
    return(x < . & x == floor(x))
}

void _dash_lpolyci_opts(string scalar unk, string scalar ptype)
{
    string rowvector toks
    string scalar    rest, w, nm, val, pw, vr, lv, msg, frac
    real scalar      i, p, x, hasp, hasv, ints

    st_local("_lpo_pwidth", "")
    st_local("_lpo_var", "")
    st_local("_lpo_rest", unk)
    st_local("_lpo_rc", "0")
    st_local("_lpo_msg", "")
    if (ptype != "lpolyci") return
    toks = _dash_rep_toks(unk, 0)
    rest = ""
    pw = ""
    vr = ""
    hasp = 0
    hasv = 0
    for (i = 1; i <= cols(toks); i++) {
        w = toks[i]
        p = strpos(w, "(")
        if (p > 1 & substr(w, strlen(w), 1) == ")") {
            nm  = substr(w, 1, p - 1)
            val = substr(w, p + 1, strlen(w) - p - 1)
            if (strlen(nm) >= 2 & nm == substr("pwidth", 1, strlen(nm))) {
                pw = val
                hasp = 1
                continue
            }
            if (strlen(nm) >= 1 & nm == substr("var", 1, strlen(nm))) {
                vr = val
                hasv = 1
                continue
            }
        }
        rest = rest + (rest == "" ? "" : " ") + w
    }
    st_local("_lpo_rest", rest)
    msg = ""
    // 1. var() must be one number
    if (hasv) {
        if (!_dash_lpo_onenum(vr, x, msg)) {
            st_local("_lpo_rc", "7")
            st_local("_lpo_msg", msg)
            return
        }
        st_local("_lpo_var", strofreal(x, "%21.0g"))
    }
    // 2. level() must be one number
    lv = strtrim(st_global("s(level)"))
    if (lv != "") {
        if (!_dash_lpo_onenum(lv, x, msg)) {
            st_local("_lpo_rc", "7")
            st_local("_lpo_msg", msg)
            return
        }
    }
    ints = _dash_lpo_isint(st_global("s(degree)")) &
           _dash_lpo_isint(st_global("s(n)"))
    if (!ints) {
        // the table refuses the malformed degree()/n() later (D7)
        if (hasp) {
            if (_dash_lpo_onenum(pw, x, msg) & x > 0) st_local("_lpo_pwidth", strofreal(x, "%21.0g"))
        }
        return
    }
    // 3. level(): no exponent, 10..99.99, at most two decimals as typed
    if (lv != "") {
        if (ustrregexm(lv, "[eEdD]")) {
            st_local("_lpo_rc", "198")
            st_local("_lpo_msg", lv + " found where number expected")
            return
        }
        x = strtoreal(lv)
        if (!(x >= 10 & x <= 99.99)) {
            st_local("_lpo_rc", "198")
            st_local("_lpo_msg", "level() must be between 10 and 99.99 inclusive")
            return
        }
        p = strpos(lv, ".")
        frac = p ? substr(lv, p + 1, .) : ""
        if (strlen(frac) > 2) {
            st_local("_lpo_rc", "198")
            st_local("_lpo_msg", "level() can have at most two digits after the decimal point")
            return
        }
    }
    // 4. pwidth() a positive number; a leading + is "expression
    // invalid", r(3000) (WP-31 C11, estimator_edges_truth.json lp.D8)
    if (hasp) {
        if (substr(strtrim(pw), 1, 1) == "+") {
            st_local("_lpo_rc", "3000")
            st_local("_lpo_msg", "expression invalid")
            return
        }
        if (!_dash_lpo_onenum(pw, x, msg) | !(x > 0)) {
            st_local("_lpo_rc", "198")
            st_local("_lpo_msg", "pwidth() must be a positive number")
            return
        }
        st_local("_lpo_pwidth", strofreal(x, "%21.0g"))
    }
}

// _dash_rep_split(v, body, sub) -- a merged option's value at its first
// comma outside quotes and parentheses: the text or list before it, and
// the sub-options after.  Returns 1 when there is a comma.
real scalar _dash_rep_split(string scalar v, string scalar body,
                            string scalar sub)
{
    real scalar p

    p = _dash_first_comma_pos(v)
    if (!p) {
        body = v
        sub  = ""
        return(0)
    }
    body = substr(v, 1, p - 1)
    sub  = substr(v, p + 1, .)
    return(1)
}

// _dash_axis_num(arg) -- the axis number twoway's _axisnum reads from
// axis(arg) (WP-29 P0.5): syntax [, AXis(integer 1)], so a whole number
// within Stata's integer bounds, -2147483648 .. 2147483647, and 1 for
// anything else -- a blank, a word, a fraction, a missing value, a number
// past the bounds (measured: axis(2.5), axis(a), axis(1e300) and
// axis(2147483648) all give axis 1, silently; axis(02), axis(2.0),
// axis(+2), axis(2e0) and axis(1.0x+1) give axis 2).
real scalar _dash_axis_num(string scalar arg)
{
    real scalar v

    v = strtoreal(strtrim(arg))
    if (v < . & v == floor(v) & v >= -2147483648 & v <= 2147483647) return(v)
    return(1)
}

// _dash_axfam() -- twoway's axis option families (graph_g.class
// ParseAndLogAxes, optnames SCale Labels MLabels TICks MTicks Title LInes),
// one row each: the family, twoway's full name after the side letter, dash's
// name, the minimum length of the whole option name (side letter included),
// twoway's order of the family, and the name an axis(2) copy is written as
// ("" when dash does not route that family).  Read by _dash_ax_parse.
string matrix _dash_axfam()
{
    return(("title",  "title",   "title",  "2", "6", "title2" \
            "label",  "labels",  "label",  "2", "2", "label2" \
            "mlabel", "mlabels", "mlabel", "3", "3", "mlabel2" \
            "tick",   "ticks",   "tick",   "4", "4", "tick2"  \
            "mtick",  "mticks",  "mtick",  "3", "5", "mtick2" \
            "line",   "lines",   "line",   "3", "7", "line2"  \
            "scale",  "scale",   "scale",  "3", "1", "scale2"))
}

// _dash_ax_word(s) -- the first blank-delimited word of s, cut at its
// first "(": the word twoway names in "invalid '<word>'".
string scalar _dash_ax_word(string scalar s)
{
    string scalar t
    real scalar   p

    t = strltrim(subinstr(s, char(9), " "))
    p = strpos(t, " ")
    if (p) t = substr(t, 1, p - 1)
    p = strpos(t, "(")
    if (p) t = substr(t, 1, p - 1)
    return(t)
}

// _dash_ax_parse(tok, fam, d, r, v, body, words, dcw, nax, n, badw, axpos)
// -- 1 when the option word tok is one of twoway's axis options (an x, t
// or y option of a family of _dash_axfam(), its name typed in lower case,
// at least the family's minimum long and a prefix of twoway's full name),
// else 0.  t is twoway's time axis, its x axis read with dates (WP-30
// P1.6: tlabels, tticks, tlines ... ; the rows of _dash_axfam serve it as
// they serve x and y, so tt, tl, tml, ttic, tmt, tli and tsc are its
// minimums).  Sets, by reference: d the side letter; r the family's row; v
// the value as typed; body the text before the first comma (not for a
// scale); words the sub-option words the axis words are read from (after
// the first comma, or every word of a scale); dcw the word after a second
// comma ("" when none -- a comma followed by blanks only is no second
// comma); nax the lower-case axis words; n the axis the first of them
// names (1 when none); badw the first axis word in capitals or second
// lower-case one, as typed, cut at "("; axpos the first axis word's place
// in words.  An axis word is ax, axi or axis, then "(".  No regex.
real scalar _dash_ax_parse(string scalar tok, string matrix fam,
                           string scalar d, real scalar r, string scalar v,
                           string scalar body, string rowvector words,
                           string scalar dcw, real scalar nax,
                           real scalar n, string scalar badw,
                           real scalar axpos)
{
    string scalar nm, full, sub, b2, s2, w, an, la, arg
    real scalar   i, j, p, mn

    if (!strpos(tok, "(")) return(0)
    nm = _dash_rep_optname(tok)
    if (nm == "" | nm != strlower(nm)) return(0)
    d = substr(nm, 1, 1)
    if (d != "x" & d != "y" & d != "t") return(0)
    r = 0
    for (i = 1; i <= rows(fam); i++) {
        full = d + fam[i, 2]
        mn   = strtoreal(fam[i, 4])
        if (strlen(nm) >= mn & strlen(nm) <= strlen(full) &
            substr(full, 1, strlen(nm)) == nm) {
            r = i
            break
        }
    }
    if (!r) return(0)
    v    = _dash_rep_value(tok)
    dcw  = ""
    body = ""
    sub  = ""
    if (fam[r, 1] == "scale") {
        // A scale's value is read after a comma twoway puts in front of
        // it, so any comma in it is a second one; a trailing one is not.
        if (_dash_rep_split(v, b2, s2)) {
            if (strtrim(s2) != "") dcw = _dash_ax_word(s2)
            sub = b2
        }
        else sub = v
    }
    else if (_dash_rep_split(v, body, sub)) {
        if (_dash_rep_split(sub, b2, s2)) {
            if (strtrim(s2) != "") dcw = _dash_ax_word(s2)
            sub = b2
        }
    }
    words = _dash_rep_toks(sub, 0)
    n     = 1
    nax   = 0
    badw  = ""
    axpos = 0
    for (j = 1; j <= cols(words); j++) {
        w = words[j]
        p = strpos(w, "(")
        if (!p) continue
        an = substr(w, 1, p - 1)
        la = strlower(an)
        if (strlen(la) < 2 | strlen(la) > 4) continue
        if (substr("axis", 1, strlen(la)) != la) continue
        if (an != la) {
            if (badw == "") badw = an
            continue
        }
        nax++
        if (nax == 1) {
            arg = substr(w, p + 1, .)
            if (substr(arg, strlen(arg), 1) == ")") arg = substr(arg, 1, strlen(arg) - 1)
            n     = _dash_axis_num(arg)
            axpos = j
        }
        else if (badw == "") badw = an
    }
    return(1)
}

// _dash_route_axis2(opts) -- the option list with each axis option's
// axis(#) applied, as twoway's ParseAndLogAxes applies it (WP-29 P0.5;
// WP-28 B3 did the titles).  It runs before -syntax- and before
// _dash_rep_reduce, whose merge would otherwise fold ylabel(10 20)
// ylabel(5000 10000, axis(2)) into one ylabel and lose the first axis's
// list.  For each x or y title, label, mlabel, tick, mtick, line and scale
// option (_dash_axfam: twoway's spellings and plurals, typed in lower
// case):
//   axis(1), or a number that is no whole number within twoway's bounds:
//       the axis word is dropped; a plural is written as dash's name
//       (ylabels(5000) is ylabel(5000), as twoway reads it);
//   axis(2): written as dash's second-axis option -- ytitle2(), ylabel2(),
//       ytick2(), yline2(), yscale2() -- the axis word dropped and the
//       other words kept, each body byte for byte;
//   axis(3) to axis(9) (WP-31 C10c): taken out of the list and recorded
//       by _dash_axisn_add, value formed as for axis 2, for the graph's
//       "axisn" object, mlabel and mtick included (WP-31 D1b; a t option
//       on those axes is left as typed);
//   axis(2) of an mlabel or mtick (WP-31 D1): xmlabel2(), ymlabel2(),
//       xmtick2(), ymtick2() alike, a t option's as the x one's (WP-31
//       D1b);
//   any other axis, a second
//       axis word, an axis word in capitals and a second comma: left as
//       typed, for _dash_axreq_check to refuse in twoway's words.
// zlabels(), zticks(), zmlabels() and zmticks() are written as zlabel(),
// ztick(), zmlabel() and zmtick(), their values as typed (WP-42 AX-12).
// Every other word, and every body, is returned byte for byte, so text
// holding "axis(2)", a quote, $ or a backtick is kept as typed.  No regex
// (regexm follows the caller's version).
string scalar _dash_route_axis2(string scalar opts)
{
    string rowvector toks, words
    string matrix    fam
    string scalar    out, tok, d, v, body, dcw, badw, rest, dn
    real scalar      i, j, r, nax, n, axpos, any, scale

    toks = _dash_rep_toks(opts, 0)
    if (cols(toks) == 0) return(opts)
    fam = _dash_axfam()
    out = ""
    any = 0
    for (i = 1; i <= cols(toks); i++) {
        tok = toks[i]
        // The z axis's plurals (WP-42 AX-12): twoway takes zlabels(),
        // zticks(), zmlabels() and zmticks() as zlabel(), ztick(),
        // zmlabel() and zmtick() (twowaygraph_g.class ZLabels ZTicks
        // ZMLabels ZMTicks); written as the singular, its value as typed.
        if (strpos(tok, "(") & anyof(("zlabels", "zticks", "zmlabels",
                                      "zmticks"), _dash_rep_optname(tok))) {
            dn = _dash_rep_optname(tok)
            toks[i] = substr(dn, 1, strlen(dn) - 1) + "(" +
                      _dash_rep_value(tok) + ")"
            any = 1
            continue
        }
        if (!_dash_ax_parse(tok, fam, d, r, v, body, words, dcw, nax, n,
                            badw, axpos)) continue
        if (dcw != "" | badw != "") continue
        scale = (fam[r, 1] == "scale")
        rest  = ""
        for (j = 1; j <= cols(words); j++) {
            if (j == axpos) continue
            rest = rest + (rest == "" ? "" : " ") + words[j]
        }
        if (n == 1) {
            dn = d + fam[r, 3]
            if (!nax) {
                // No axis word: only a plural is renamed, its value as typed.
                if (_dash_rep_optname(tok) == d + fam[r, 2] & fam[r, 2] != fam[r, 3]) {
                    toks[i] = dn + "(" + v + ")"
                    any = 1
                }
                continue
            }
        }
        // A t option's mlabel or mtick on axis 2 is the x one's (WP-31
        // D1b, measured: tmlabel(##2, axis(2)) draws as xmlabel(##2,
        // axis(2)), axisn_minor_truth.json m3.tmlabel); dash has no t key
        // for them, so it is recorded as a "t" row, whose dates
        // _dash_taxis_fold reads (WP-31 C10e) before it joins xmlabel2().
        else if (n == 2 & fam[r, 6] != "" & !(d == "t" &
                 anyof(("mlabel", "mtick"), fam[r, 1]))) {
            dn = d + fam[r, 6]
        }
        // Axes 3-9 (WP-31 C10c), their mlabel and mtick too (WP-31 D1b),
        // and the t options there (WP-31 C10e: "t" rows, folded onto the
        // x axis by _dash_taxis_fold).
        else if ((n >= 3 & n <= 9 & fam[r, 6] != "") | (n == 2 & d == "t")) {
            // Axes three to nine (WP-31 C10c): the option leaves the text
            // and is recorded for the graph's "axisn" object
            // (_dash_axisn_json), its value formed as an axis-2 copy's.
            _dash_axisn_add(d, n, fam[r, 1], (scale ? rest :
                            body + (rest == "" ? "" : ", " + rest)))
            toks[i] = ""
            any = 1
            continue
        }
        else continue
        toks[i] = dn + "(" + (scale ? rest :
                  body + (rest == "" ? "" : ", " + rest)) + ")"
        any = 1
    }
    // Nothing routed: the list exactly as typed, spacing and all (and no
    // join, which the 10,000-copy exhaustion case TP-14e times).
    if (!any) return(opts)
    for (i = 1; i <= cols(toks); i++) {
        if (toks[i] == "") continue
        out = out + (out == "" ? "" : " ") + toks[i]
    }
    return(out)
}

// _dash_axreq_clear(), _dash_axreq_add(opts, seg) and
// _dash_axreq_check(ys, xs) -- twoway's refusals of an axis option
// (WP-29 P0.5).  _dash_axreq_add records, from the RAW option text of plot
// segment seg (the options after the top-level comma are segment n_segs+1,
// read after every segment, as twoway reads them), one row per axis option
// in the external string matrix _dash_axreq: side (1 x, 2 t, 3 y: twoway's
// X, T, Y order, f12/f13 of taxis_truth.json; a t option names the x
// axes, "tlabels(...) not allowed, xaxis3 does not exist"), twoway's
// family order (scale 1 .. lines 7), seg, the word's place, the axis
// number, the name twoway's message uses (ylabels, ytitle, yscale ...),
// the value as typed, the word after a second comma and the first axis
// word in capitals or second lower-case one.  dash's own ytitle2() ...
// are no axis option of twoway's and are not recorded.  _dash_axreq_check
// orders the rows as twoway does -- side, family, segment, place -- and
// refuses the first that fails, testing in twoway's order: a second comma
// ("invalid '<word>'"), an axis no layer uses ("ylabels(...) not allowed,
// yaxis3 does not exist"; ys and xs are the layers' axes), then a bad axis
// word ("option AXIS() not allowed").  Each message goes through
// _dash_say, so the user's text is shown as typed.  The matrix is cleared
// at the start of every graph command and after the check, so no typed
// text is kept.  Linear: one pass over the words into a block sized by
// their count.
void _dash_axreq_clear()
{
    external string matrix _dash_axreq

    _dash_axreq = J(0, 12, "")
    _dash_subreq_clear()
}

void _dash_axreq_add(string scalar opts, real scalar seg)
{
    external string matrix _dash_axreq
    string rowvector toks, words
    string matrix    fam, blk
    string rowvector snames
    string scalar    d, v, body, dcw, badw, sm, sm2, lb, lb2, ls2, lnone
    string rowvector kept
    real scalar      i, j, k, r, nax, n, axpos, sat, nex

    _dash_subreq_add(opts, seg)
    toks = _dash_rep_toks(opts, 0)
    if (cols(toks) == 0) return
    fam = _dash_axfam()
    blk = J(cols(toks), 12, "")
    k   = 0
    for (i = 1; i <= cols(toks); i++) {
        if (!_dash_ax_parse(toks[i], fam, d, r, v, body, words, dcw, nax, n,
                            badw, axpos)) continue
        k++
        // Column 10 (WP-30 P1.19): twoway's refusal of a label, mlabel,
        // tick or mtick sub-option (_dash_so_resolve's message), or "";
        // and of a scale word (WP-30 P1.18a: yscale(OFF), xscale(bogus),
        // yscale(alt alt) are "option OFF not allowed", r(198)).
        sm = ""
        if (anyof(("label", "mlabel", "tick", "mtick"), fam[r, 1]) &
            cols(words)) {
            if (_dash_so_resolve(words, J(1, cols(words), 1), "axlabel",
                                 snames, sm, sat) == 0) sm = ""
        }
        else if (fam[r, 1] == "scale" & cols(words)) {
            // WP-44 AX-10: the transform words as twoway's syntax binds
            // them, then its opts_exclusive over them, in one copy.
            sm = _dash_scale_exclusive(words, kept)
            if (_dash_so_resolve(kept, J(1, cols(kept), 1), "axscale",
                                 snames, sm2, sat) != 0) sm = sm2
        }
        // Columns 11-12 (WP-30 P1.21a): a line's positions, stripped, and
        // "1" when there are none to check.  twoway's
        // _gs_parse_and_log_lines reads the sub-options first ("option
        // foo not allowed"; a second extend, typed as ex or extend, too,
        // where a second noextend is accepted), then an empty list given
        // a comma ("something required", r(100), tested first), then the
        // positions through numlist (_dash_axreq_check hands them back).
        lb    = ""
        lnone = ""
        if (fam[r, 1] == "line") {
            if (_dash_rep_split(v, lb2, ls2)) {
                if (strtrim(lb2) == "") sm = "100|something required"
            }
            else lb2 = v
            lb = strtrim(lb2)
            // A tline()'s positions are dates: _dash_taxis_fold reads them.
            if (lb == "" | d == "t") lnone = "1"
            if (sm == "" & cols(words)) {
                if (_dash_so_resolve(words, J(1, cols(words), 1), "refline",
                                     snames, sm, sat) == 0) {
                    sm  = ""
                    nex = 0
                    for (j = 1; j <= cols(words); j++) {
                        if (snames[j] != "extend") continue
                        nex++
                        if (nex == 2) {
                            sm = "option " + strtrim(words[j]) + " not allowed"
                            break
                        }
                    }
                }
            }
        }
        blk[k, .] = ((d == "x" ? "1" : (d == "t" ? "2" : "3")), fam[r, 5], strofreal(seg),
                     strofreal(i), strofreal(n, "%21.0f"), d + fam[r, 2], v,
                     dcw, badw, sm, lb, lnone)
    }
    if (!k) return
    blk = blk[|1, 1 \ k, 12|]
    if (rows(_dash_axreq) == 0 | cols(_dash_axreq) != 12) _dash_axreq = blk
    else _dash_axreq = _dash_axreq \ blk
}

real scalar _dash_axreq_check(string scalar ys, string scalar xs)
{
    external string matrix _dash_axreq
    string matrix    a
    string scalar    d
    real rowvector   yset, xset, set
    real colvector   o
    real scalar      i, n

    if (rows(_dash_axreq) == 0 | cols(_dash_axreq) != 12) {
        _dash_axreq = J(0, 12, "")
        return(0)
    }
    a    = _dash_axreq
    yset = strtoreal(tokens(ys))
    xset = strtoreal(tokens(xs))
    if (cols(yset) == 0) yset = 1
    if (cols(xset) == 0) xset = 1
    o = order(strtoreal(a[., (1, 2, 3, 4)]), (1, 2, 3, 4))
    for (i = 1; i <= rows(o); i++) {
        d = (a[o[i], 1] == "3" ? "y" : "x")
        if (a[o[i], 8] != "") {
            _dash_say("err", "invalid '", a[o[i], 8], "'")
            _dash_axreq_clear()
            return(198)
        }
        n   = strtoreal(a[o[i], 5])
        set = (d == "x" ? xset : yset)
        if (!anyof(set, n)) {
            _dash_say("err", a[o[i], 6] + "(", a[o[i], 7],
                      ") not allowed, " + d + "axis" +
                      strtrim(strofreal(n, "%11.0f")) + " does not exist")
            _dash_axreq_clear()
            return(198)
        }
        if (a[o[i], 9] != "") {
            _dash_say("err", "option ", a[o[i], 9], "() not allowed")
            _dash_axreq_clear()
            return(198)
        }
        if (substr(a[o[i], 10], 1, 4) == "100|") {
            _dash_say("err", "", substr(a[o[i], 10], 5, .), "")
            _dash_axreq_clear()
            return(100)
        }
        if (a[o[i], 10] != "") {
            _dash_say("err", "", a[o[i], 10], "")
            _dash_axreq_clear()
            return(198)
        }
        // A line's positions (WP-30 P1.21a): text numlist must never see
        // is refused here; the rest goes back to dash.ado's
        // _dash_line_check (locals _ln_text, _ln_row), which runs Stata's
        // own numlist and marks the row with _dash_axreq_accept_line.
        if (a[o[i], 2] == "7" & a[o[i], 12] == "") {
            if (_dash_so_unsafe(a[o[i], 11])) {
                _dash_say("err", "invalid line argument, ", a[o[i], 11], "")
                _dash_axreq_clear()
                return(198)
            }
            st_local("_ln_text", a[o[i], 11])
            st_local("_ln_row", strofreal(o[i]))
            return(-1)
        }
    }
    _dash_axreq = J(0, 12, "")
    return(0)
}

// ==== axes three to nine (WP-31 C10c) ======================================
// _dash_axisn_clear(), _dash_axisn_add(d, n, family, value) and
// _dash_axisn_json(): the axis options written for axes 3-9 travel in the
// graph's "axisn" object, {"y3":{"label":"...","title":"..."},...}, one
// entry per (letter, axis, family); copies merge, in the order they were
// typed, as the axis-2 key's category merges them (_dash_rep_merge).
// Values are the user's text, escaped by _dash_json_escape; nothing here is run.
void _dash_axisn_clear()
{
    external string matrix _dash_axisn
    _dash_axisn = J(0, 4, "")
}

void _dash_axisn_add(string scalar d, real scalar n, string scalar family,
                     string scalar value)
{
    external string matrix _dash_axisn
    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 4) _dash_axisn = J(0, 4, "")
    _dash_axisn = _dash_axisn \ (d, strofreal(n), family, value)
}

// _dash_axisn_tf_out() and _dash_axisn_tf_in() (WP-31 C10e): the x and t
// rows of axes 3-9, and the t mlabel/mtick rows of axis 2, as the globals
// _dash_taxis_fold reads and writes -- dash__tf_<x|t><family>_<n> (axis 2:
// dash__tf_t<family>2) -- copies merged in the order typed.  _tf_out moves
// them out of the matrix (every "t" row and the x rows of axes 3-9);
// _tf_in puts the folded x values back as one row per axis and family.
// Values are the user's text, moved by value; nothing here is run.
void _dash_axisn_tf_out()
{
    external string matrix _dash_axisn
    string matrix keep
    string scalar g
    real scalar   i, n

    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 4) return
    keep = J(0, 4, "")
    for (i = 1; i <= rows(_dash_axisn); i++) {
        n = strtoreal(_dash_axisn[i, 2])
        if (_dash_axisn[i, 1] == "t" | (_dash_axisn[i, 1] == "x" & n >= 3)) {
            g = "dash__tf_" + _dash_axisn[i, 1] + _dash_axisn[i, 3] +
                (n == 2 ? "2" : "_" + _dash_axisn[i, 2])
            st_global(g, _dash_rep_merge("x" + _dash_axisn[i, 3] + "2",
                                         st_global(g), _dash_axisn[i, 4]))
        }
        else keep = keep \ _dash_axisn[i, .]
    }
    _dash_axisn = keep
}

void _dash_axisn_tf_in()
{
    external string matrix _dash_axisn
    string rowvector families
    string scalar    g, v
    real scalar      j, n

    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 4) _dash_axisn = J(0, 4, "")
    families = ("title", "label", "tick", "line", "scale", "mlabel", "mtick")
    for (n = 3; n <= 9; n++) {
        for (j = 1; j <= cols(families); j++) {
            g = "dash__tf_x" + families[j] + "_" + strofreal(n)
            v = st_global(g)
            if (v != "") _dash_axisn = _dash_axisn \ ("x", strofreal(n), families[j], v)
            st_global(g, "")
            st_global("dash__tf_t" + families[j] + "_" + strofreal(n), "")
        }
    }
}

string scalar _dash_axisn_json()
{
    external string matrix _dash_axisn
    string scalar    out, name, fams, v
    string rowvector names, families
    real scalar      i, j, k, seen

    if (rows(_dash_axisn) == 0 | cols(_dash_axisn) != 4) return("")
    families = ("title", "label", "tick", "line", "scale", "mlabel", "mtick")
    names = J(1, 0, "")
    for (i = 1; i <= rows(_dash_axisn); i++) {
        // A "t" row not folded (WP-31 C10e) is no axis of the graph's.
        if (!anyof(("x", "y"), _dash_axisn[i, 1])) continue
        name = _dash_axisn[i, 1] + _dash_axisn[i, 2]
        if (!anyof(names, name)) names = names, name
    }
    names = sort(names', 1)'
    out = "{"
    for (i = 1; i <= cols(names); i++) {
        fams = ""
        for (j = 1; j <= cols(families); j++) {
            v = ""
            seen = 0
            for (k = 1; k <= rows(_dash_axisn); k++) {
                if (_dash_axisn[k, 1] + _dash_axisn[k, 2] != names[i] |
                    _dash_axisn[k, 3] != families[j]) continue
                v = (seen ? _dash_rep_merge(_dash_axisn[k, 1] + families[j] + "2",
                                            v, _dash_axisn[k, 4]) : _dash_axisn[k, 4])
                seen = 1
            }
            if (!seen) continue
            // A global in an axis title or label is its value, as twoway
            // reads a graph text option again (WP-31 D13b), its =exp runs
            // evaluated by the safe evaluator (WP-43 LT-20, P4-7).
            // Then {ccl name} is c(name) (WP-31 E9, smcl_more_truth.json
            // axis3.ytitle, axis3.ylabel).
            if (anyof(("title", "label", "mlabel"), families[j])) v = _dash_gt_ccl(_dash_at_globals(v, 1))
            // mlabel is written "mlab" (WP-31 D1b): a key "mlabel" is a
            // marker-label variable to _dash_extract_vars.
            fams = fams + (fams == "" ? "" : ",") + char(34) +
                   (families[j] == "mlabel" ? "mlab" : families[j]) +
                   char(34) + ":" + char(34) + _dash_json_escape(v) + char(34)
        }
        out = out + (i > 1 ? "," : "") + char(34) + names[i] + char(34) +
              ":{" + fams + "}"
    }
    return(out + "}")
}

// _dash_axreq_accept_line(row) -- marks row of _dash_axreq as a line
// whose positions Stata's numlist read (WP-30 P1.21a).
void _dash_axreq_accept_line(real scalar row)
{
    external string matrix _dash_axreq

    if (row >= 1 & row <= rows(_dash_axreq) & cols(_dash_axreq) == 12) {
        _dash_axreq[row, 12] = "1"
    }
}

// ==== The t-options' date literals (WP-30 P1.6) ==========================
// twoway folds tlabel(), ttick(), tmlabel(), tmtick(), ttitle(), tscale()
// and tline() onto the x axis after the x options (graph_g.class "time
// axis options, override the -x- axis options"), reading each date
// literal through _date2elapsed.ado in the unit of the axis's label
// format: 2002m1 is 504 on a %tm axis (test/fixtures/taxis_truth.json,
// StataNow 19.5).  dash.ado's _dash_taxis_fold folds them at registration
// with these functions.  A token is read with Mata's string date
// functions, as data, behind a whitelist, and never put to _stata(),
// stata() or a command line (critic C3); a number is a number first, so
// 01012001 stays 1012001 (critic C2).  No regular expression; each value
// is read once, linear in its length.

// _dash_taxis_unit(fmt, family) -- the date unit twoway reads a literal in
// on an axis whose label format is fmt: "d" (%td, %d), "w", "m", "q", "h",
// "y", or "" (numbers only: %tc, %tC, %tb and every numeric format).
// family 1 is a label or tick list (_date2elapsed's map, which reads %-tm
// as %tm); family 2 a line or a scale range (axis.class get_time_format,
// which tests only the prefixes %t and %d, so %-tm has no unit there, and
// a %tc, %tC or %tb axis gives "c": a time format with no literal form,
// whose lines fail as numlist fails, "invalid line argument, ...").
string scalar _dash_taxis_unit(string scalar fmt, real scalar family)
{
    string scalar f, c

    f = strtrim(fmt)
    if (family == 2 & substr(f, 1, 2) != "%t" & substr(f, 1, 2) != "%d") {
        return("")
    }
    if (substr(f, 1, 1) == "%") f = substr(f, 2, .)
    if (substr(f, 1, 1) == "-") f = substr(f, 2, .)
    if (substr(f, 1, 1) == "d") return("d")
    if (substr(f, 1, 1) != "t") return("")
    c = substr(f, 2, 1)
    if (anyof(("d", "w", "m", "q", "h", "y"), c)) return(c)
    return(family == 2 ? "c" : "")
}

// _dash_tdate_value(tok, unit, val) -- 1 when tok is a number, a missing
// value or a date literal of unit (val set to its value); 2 when it is a
// date literal of some other unit, or unit has none (unit "", "c", "y");
// 3 when it is neither.  The number first (strtoreal); then the whitelist
// gate -- 1 to 40 bytes of 0-9, A-Z, a-z and . + - * / @ = _, as twoway's
// pseudo-functions read separators freely (2000x1, 2000/1, 2000@1 are all
// 480; scalar s = m(2000x1), measured) -- and only then Mata's date(),
// weekly(), monthly(), quarterly() and halfyearly() over the token as a
// string; an integer answer is a date.  A token the gate refuses is never
// evaluated.  S56's ttext() reads its position with it too.  A token in
// parentheses holding a blank, (1 jan 2001), is its inner text read with
// the blank added to the gate, as twoway's datelist binds a date with
// blanks (WP-44 DG-4: test/fixtures/date_axis_rule_truth.json dg4.*); a
// comma inside stays refused (dg4.DT06).
real scalar _dash_tdate_value(string scalar tok, string scalar unit,
                              real scalar val)
{
    string scalar  t, ok
    real scalar    v, i

    t  = strtrim(tok)
    ok = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.+-*/@=_"
    if (strlen(t) > 2 & substr(t, 1, 1) == "(" &
        substr(t, strlen(t), 1) == ")" &
        strpos(substr(t, 2, strlen(t) - 2), " ")) {
        t  = strtrim(substr(t, 2, strlen(t) - 2))
        ok = ok + " "
        if (strlen(t) < 1 | strlen(t) > 40) return(3)
        for (i = 1; i <= strlen(t); i++) {
            if (!strpos(ok, substr(t, i, 1))) return(3)
        }
        return(_dash_tdate_lit(t, unit, val))
    }
    v = strtoreal(t)
    if (v < .) {
        val = v
        return(1)
    }
    if (t == "." | (strlen(t) == 2 & substr(t, 1, 1) == "." &
        strpos("abcdefghijklmnopqrstuvwxyz", substr(t, 2, 1)))) {
        val = v
        return(1)
    }
    if (strlen(t) < 1 | strlen(t) > 40) return(3)
    for (i = 1; i <= strlen(t); i++) {
        if (!strpos(ok, substr(t, i, 1))) return(3)
    }
    return(_dash_tdate_lit(t, unit, val))
}

// _dash_tdate_lit(t, unit, val) -- _dash_tdate_value's last step, for a
// token its gate passed: Mata's date(), weekly(), monthly(), quarterly()
// and halfyearly() over t as a string; 1 (val set) for an integer answer
// in unit, 2 for one in another unit, else 3.
real scalar _dash_tdate_lit(string scalar t, string scalar unit,
                            real scalar val)
{
    real scalar    v, i
    real rowvector w

    w = (date(t, "DMY"), weekly(t, "YW"), monthly(t, "YM"),
         quarterly(t, "YQ"), halfyearly(t, "YH"))
    // (A chain of ?: reads unit == "d" ? .. : unit == .. wrongly in
    // Mata, so the unit is looked up.)
    i = strpos("dwmqh", unit)
    v = ((unit != "" & strlen(unit) == 1 & i > 0) ? w[i] : .)
    if (v < . & v == floor(v)) {
        val = v
        return(1)
    }
    for (i = 1; i <= 5; i++) if (w[i] < . & w[i] == floor(w[i])) return(2)
    return(3)
}

// _dash_tdate_toks(seg) -- seg split at the blanks outside parentheses (a
// depth counter; a quote has no meaning here), so (1 jan 2001) and
// td(1jan2001) are one token each and two dates a blank apart are two
// (WP-44 DG-4).  Linear in seg's length; tokens(seg) for seg with no
// parenthesis.
string rowvector _dash_tdate_toks(string scalar seg)
{
    string rowvector out
    string scalar    cur, c
    real scalar      i, depth

    if (!strpos(seg, "(")) return(tokens(seg))
    out   = J(1, 0, "")
    cur   = ""
    depth = 0
    for (i = 1; i <= strlen(seg); i++) {
        c = substr(seg, i, 1)
        if (c == "(") depth++
        else if (c == ")" & depth > 0) depth--
        if ((c == " " | c == char(9)) & depth == 0) {
            if (cur != "") out = out, cur
            cur = ""
            continue
        }
        cur = cur + c
    }
    if (cur != "") out = out, cur
    return(out)
}

// _dash_tdate_tok(tok, unit, out, bad, single) -- one position slot of a
// tick, label or line list: a position, a position in parentheses, an
// A(d)B rule ((A)(d)(B) too, c55) or a numeric A/B range.  Returns
// _dash_tdate_value's rating (a rule takes its worst end; its step must
// be a number, else 3), sets out to the slot with each position written
// as the number twoway reads (%21.0g), bad to the token at fault, and
// single to 1 for a lone position (a label may follow it).
real scalar _dash_tdate_tok(string scalar tok, string scalar unit,
                            string scalar out, string scalar bad,
                            real scalar single)
{
    string scalar a, d, b, rest
    real scalar   p, q, k, ka, kb, va, vb, v

    single = 0
    out    = tok
    bad    = tok
    p      = strpos(tok, "/")
    if (p & !strpos(tok, "(")) {
        if (strtoreal(substr(tok, 1, p - 1)) < . &
            strtoreal(substr(tok, p + 1, .)) < .) return(1)
    }
    if (!strpos(tok, "(")) {
        k = _dash_tdate_value(tok, unit, v)
        if (k == 1) {
            out    = strtrim(strofreal(v, "%21.0g"))
            single = 1
        }
        return(k)
    }
    if (substr(tok, 1, 1) == "(") {
        q = strpos(tok, ")")
        if (!q) return(3)
        a    = substr(tok, 2, q - 2)
        rest = substr(tok, q + 1, .)
        if (rest == "") {
            // WP-44 DG-4: (1 jan 2001), its blanks bound by the parentheses.
            k = _dash_tdate_value(strpos(a, " ") ? "(" + a + ")" : a, unit, v)
            if (k == 1) {
                out    = strtrim(strofreal(v, "%21.0g"))
                single = 1
            }
            else bad = a
            return(k)
        }
    }
    else {
        p    = strpos(tok, "(")
        a    = substr(tok, 1, p - 1)
        rest = substr(tok, p, .)
    }
    if (substr(rest, 1, 1) != "(") return(3)
    q = strpos(rest, ")")
    if (!q) return(3)
    d = substr(rest, 2, q - 2)
    b = substr(rest, q + 1, .)
    if (substr(b, 1, 1) == "(" & substr(b, strlen(b), 1) == ")") {
        b = substr(b, 2, strlen(b) - 2)
    }
    if (a == "" | b == "" | strtoreal(d) >= .) return(3)
    ka = _dash_tdate_value(a, unit, va)
    kb = _dash_tdate_value(b, unit, vb)
    if (ka == 3 | kb == 3) return(3)
    if (ka == 2 | kb == 2) {
        bad = (ka == 2 ? a : b)
        return(2)
    }
    out = strtrim(strofreal(va, "%21.0g")) + "(" + strtrim(d) + ")" +
          strtrim(strofreal(vb, "%21.0g"))
    return(1)
}

// _dash_tdate_ticks(opt, unit) -- the caller's local _td_in, the value of
// tlabel(), ttick(), tmlabel() or tmtick(), with every position converted
// (twoway's tickset: rules, then a list of positions each optionally
// followed by its label), into _td_out; _td_rc 0 or 198 and _td_msg
// twoway's first error line (e01/e04/e10/e19/e27: "invalid label
// specifier, :  <tok>:"; a date of another unit, "invalid ticklist
// "<tok>" must be a number or valid argument for <u>() function", or
// "... must be number" on a numeric axis).  #N, ##N, minmax, none and an
// empty list are copied; the sub-options after the first comma are copied
// as typed.  opt names the option for nothing but the caller's notes.
void _dash_tdate_ticks(string scalar opt, string scalar unit)
{
    string scalar    v, body, sub, out, o, bad, tok, msg, sm
    string rowvector t, w, sn
    real scalar      comma, i, k, single, prev, rc, sat

    v     = st_local("_td_in")
    comma = _dash_rep_split(v, body, sub)
    t     = _dash_rep_toks(body, 0)
    out   = ""
    rc    = 0
    msg   = ""
    prev  = 0
    if (cols(t) == 1) {
        if (substr(t[1], 1, 1) == "#" | anyof(("minmax", "none", "."),
            strlower(t[1]))) t = J(1, 0, "")
    }
    if (cols(t) == 0) out = body
    for (i = 1; i <= cols(t); i++) {
        tok = t[i]
        if (substr(tok, 1, 1) == char(34) | substr(tok, 1, 2) == char(96) + char(34)) {
            if (!prev) {
                rc  = 198
                msg = "invalid label specifier, :  " + invtokens(t[|i \ cols(t)|]) + ":"
                break
            }
            out  = out + " " + tok
            prev = 0
            continue
        }
        k = _dash_tdate_tok(tok, unit, o, bad, single)
        if (k == 3) {
            rc  = 198
            msg = "invalid label specifier, :  " + invtokens(t[|i \ cols(t)|]) + ":"
            break
        }
        if (k == 2) {
            rc  = 198
            msg = "invalid ticklist " + char(34) + bad + char(34) + " must be " +
                  ((unit == "" | unit == "c" | unit == "y") ? "number" :
                   "a number or valid argument for " + unit + "() function")
            break
        }
        out  = out + (out == "" ? "" : " ") + o
        prev = single
    }
    // The sub-options, as twoway's tickset reads them (e28:
    // tlabel(2000m1,2001m1) is "option 2001m1 not allowed").
    if (!rc & comma) {
        w = _dash_rep_toks(sub, 0)
        if (cols(w)) {
            if (_dash_so_resolve(w, J(1, cols(w), 1), "axlabel", sn, sm,
                                 sat) != 0) {
                rc  = 198
                msg = sm
            }
        }
    }
    st_local("_td_out", strtrim(out) + (comma ? "," + sub : ""))
    st_local("_td_rc", strofreal(rc))
    st_local("_td_msg", msg)
}

// _dash_tdate_lines(unit) -- the caller's local _td_in, a tline() value
// (its copies joined ", " by _dash_rep_merge), cut at its top-level
// commas into _td_n pieces _td_s<i>, each a copy's positions converted
// (_td_k<i> 1) or a sub-option piece copied (_td_k<i> 0; a copy's
// positions are its first piece and any later piece that starts with a
// digit, a sign, a dot or a parenthesis, as _dash_line_expand reads
// them).  dash.ado expands each positions piece with numlist.  _td_rc 0
// or 198, _td_msg twoway's words (e02/e08/e18: "invalid line argument,
// <the positions>"; e05/c25d: "invalid argument "<tok>" must be a number
// or valid argument for <u>() function"; f01/g02, a numeric or %-t axis:
// "invalid number, (<tok>)"; a %tc axis: "invalid line argument, ...").
void _dash_tdate_lines(string scalar unit)
{
    string scalar    v, seg, rest, out, o, bad, msg
    string rowvector t
    real scalar      p, n, i, k, single, rc, first

    v     = st_local("_td_in")
    rest  = v
    n     = 0
    rc    = 0
    msg   = ""
    first = 1
    while (rest != "" | first) {
        p = _dash_first_comma_pos(rest)
        if (p) {
            seg  = strtrim(substr(rest, 1, p - 1))
            rest = substr(rest, p + 1, .)
        }
        else {
            seg  = strtrim(rest)
            rest = ""
        }
        n++
        if (!first & !(seg != "" & strpos("0123456789+-.(", substr(seg, 1, 1)))) {
            st_local("_td_s" + strofreal(n), seg)
            st_local("_td_k" + strofreal(n), "0")
            continue
        }
        first = 0
        t   = _dash_tdate_toks(seg)
        out = ""
        for (i = 1; i <= cols(t) & !rc; i++) {
            k = _dash_tdate_tok(t[i], unit, o, bad, single)
            if (k == 1) out = out + (out == "" ? "" : " ") + o
            else if (k == 2 & unit != "" & unit != "c") {
                rc  = 198
                msg = "invalid argument " + char(34) + bad + char(34) +
                      " must be a number or valid argument for " + unit +
                      "() function"
            }
            else if (k == 2 & unit == "") {
                rc  = 198
                msg = "invalid number, (" + bad + ")"
            }
            else {
                rc  = 198
                msg = "invalid line argument, " + seg
            }
        }
        if (rc) break
        st_local("_td_s" + strofreal(n), out)
        st_local("_td_k" + strofreal(n), "1")
    }
    st_local("_td_n", strofreal(n))
    st_local("_td_rc", strofreal(rc))
    st_local("_td_msg", msg)
}

// _dash_tdate_range(unit) -- the caller's local _td_in, a tscale() value,
// into _td_out: every range() word's positions converted (unit as
// _dash_taxis_unit(fmt, 2) gives it) and the words made one range(), the
// union of their positions as twoway draws repeated ranges (c48: range(lo
// hi), or range(v) for one position), at the first one's place; every
// other word copied.  A position that is no number of the axis's unit is
// _td_rc 121, "range() invalid -- invalid numlist" (e03, c13, g03).
void _dash_tdate_range(string scalar unit)
{
    string rowvector w, t
    string scalar    out, nm
    real scalar      i, j, p, lo, hi, n, at, v, rc

    w   = _dash_rep_toks(st_local("_td_in"), 0)
    out = ""
    lo  = .
    hi  = .
    n   = 0
    at  = 0
    rc  = 0
    for (i = 1; i <= cols(w); i++) {
        p  = strpos(w[i], "(")
        nm = (p ? strlower(substr(w[i], 1, p - 1)) : "")
        if (!p | _dash_so_canon(nm, "axscale") != "range") continue
        if (!at) at = i
        t = _dash_tdate_toks(_dash_rep_value(w[i]))
        for (j = 1; j <= cols(t); j++) {
            if (_dash_tdate_value(t[j], unit, v) != 1 | v >= .) {
                rc = 121
                break
            }
            n++
            lo = (lo >= . ? v : min((lo, v)))
            hi = (hi >= . ? v : max((hi, v)))
        }
        if (rc) break
    }
    for (i = 1; i <= cols(w) & !rc; i++) {
        p  = strpos(w[i], "(")
        nm = (p ? strlower(substr(w[i], 1, p - 1)) : "")
        if (p & _dash_so_canon(nm, "axscale") == "range") {
            if (i != at | !n) continue
            out = out + (out == "" ? "" : " ") + "range(" +
                  strtrim(strofreal(lo, "%21.0g")) +
                  (n > 1 ? " " + strtrim(strofreal(hi, "%21.0g")) : "") + ")"
            continue
        }
        out = out + (out == "" ? "" : " ") + w[i]
    }
    st_local("_td_out", out)
    st_local("_td_rc", strofreal(rc))
    st_local("_td_msg", rc ? "range() invalid -- invalid numlist" : "")
}

// _dash_taxis_fmt(v) -- the argument of the last format() among the
// sub-options of the label or tick value v (format, for, forma, ...: the
// axis-label table's spellings), or "" when there is none.  twoway's
// tickset keeps the label format its last format() set (tickset_g.class
// 1129-1180; taxis_truth.json k01-k07), and _dash_taxis_fold reads the
// t-options' dates in it (WP-30 P1.6).
string scalar _dash_taxis_fmt(string scalar v)
{
    string rowvector w
    string scalar    body, sub, out
    real scalar      i, p

    out = ""
    if (!_dash_rep_split(v, body, sub)) return(out)
    w = _dash_rep_toks(sub, 0)
    for (i = 1; i <= cols(w); i++) {
        p = strpos(w[i], "(")
        if (!p) continue
        if (_dash_so_canon(substr(w[i], 1, p - 1), "axlabel") == "format") {
            out = strtrim(_dash_rep_value(w[i]))
        }
    }
    return(out)
}

// _dash_xdate_find(v, family) -- 1 when the value v of an x label or tick
// option (family 1), line option (2) or scale (3) holds a date literal in
// a position slot (_dash_tdate_tok rates it 2 with no unit), which twoway
// refuses there: the X options read no dates (c11-c13: "invalid label
// specifier, :  <tok>:", "invalid line argument, <tok>", r(198); "range()
// invalid -- invalid numlist", r(121)).  Sets the caller's local _xd_tok
// to the token (a whole A(d)B rule, as c11 names it).
real scalar _dash_xdate_find(string scalar v, real scalar family)
{
    string rowvector t, tt
    string scalar    body, sub, o, bad, nm
    real scalar      i, j, single, p, x

    if (family == 3) {
        t = _dash_rep_toks(v, 0)
        for (i = 1; i <= cols(t); i++) {
            p  = strpos(t[i], "(")
            nm = (p ? strlower(substr(t[i], 1, p - 1)) : "")
            if (!p | _dash_so_canon(nm, "axscale") != "range") continue
            tt = tokens(_dash_rep_value(t[i]))
            for (j = 1; j <= cols(tt); j++) {
                if (_dash_tdate_value(tt[j], "", x) == 2) {
                    st_local("_xd_tok", tt[j])
                    return(1)
                }
            }
        }
        return(0)
    }
    (void) _dash_rep_split(v, body, sub)
    t = (family == 2 ? tokens(body) : _dash_rep_toks(body, 0))
    for (i = 1; i <= cols(t); i++) {
        if (substr(t[i], 1, 1) == char(34) | substr(t[i], 1, 1) == char(96)) continue
        if (_dash_tdate_tok(t[i], "", o, bad, single) == 2) {
            st_local("_xd_tok", t[i])
            return(1)
        }
    }
    return(0)
}

// ==== twoway's sub-option tables and resolver (WP-30 P1.19) ==============
// The Mata twins of dash_render.py's _DASH_*_SUBOPT_TABLE, _dash_subopt_canon
// and _dash_subopt_resolve.  A row is (full, minimum, stage, kind, star,
// check): kind "w" a word, "a" an argument once per stage, "r" a repeatable
// argument; star "1" when the stage passes what it does not take on; check
// "", "N1"/"NL" (a numlist, checked by dash.ado's _dash_subopt_check) or
// "R"/"I" (a real/integer literal).  No regexm: it follows the caller's
// version.

// _dash_so_rows(fam) -- the rows of family fam: legend, axlabel, axscale,
// refline, title, axtitle or textbox; J(0, 6, "") for any other.
string matrix _dash_so_rows(string scalar fam)
{
    string matrix t

    t = J(0, 6, "")
    if (fam == "legend") {
        t = t \ ("position", "pos", "1", "a", "1", "" \
                  "ring", "ring", "1", "a", "1", "" \
                  "style", "sty", "1", "a", "1", "" \
                  "order", "order", "1", "a", "1", "" \
                  "showindex", "showindex", "1", "w", "1", "" \
                  "nospan", "nospan", "1", "w", "1", "")
        t = t \ ("span", "span", "1", "w", "1", "" \
                  "region", "reg", "2", "r", "1", "" \
                  "nodrawview", "nodrawv", "3", "w", "1", "" \
                  "drawview", "drawv", "3", "w", "1", "" \
                  "all", "all", "3", "w", "1", "" \
                  "styleonly", "styleonly", "3", "w", "1", "")
        t = t \ ("holes", "hol", "3", "a", "1", "NL" \
                  "textwidth", "textw", "3", "a", "1", "" \
                  "xoffset", "xoffset", "3", "a", "1", "R" \
                  "yoffset", "yoffset", "3", "a", "1", "R" \
                  "style", "sty", "3", "a", "1", "" \
                  "rows", "r", "3", "a", "1", "N1")
        t = t \ ("nocolfirst", "nocolf", "3", "w", "1", "" \
                  "colfirst", "colf", "3", "w", "1", "" \
                  "cols", "c", "3", "a", "1", "N1" \
                  "notextfirst", "notextf", "3", "w", "1", "" \
                  "textfirst", "textf", "3", "w", "1", "" \
                  "nostacked", "nostac", "3", "w", "1", "")
        t = t \ ("stacked", "stac", "3", "w", "1", "" \
                  "rowgap", "rowg", "3", "a", "1", "" \
                  "colgap", "colg", "3", "a", "1", "" \
                  "keygap", "keyg", "3", "a", "1", "" \
                  "symplacement", "symp", "3", "a", "1", "" \
                  "symxsize", "symx", "3", "a", "1", "")
        t = t \ ("symysize", "symy", "3", "a", "1", "" \
                  "noforcesize", "noforces", "3", "w", "1", "" \
                  "forcesize", "forces", "3", "w", "1", "" \
                  "bmargin", "bm", "3", "a", "1", "" \
                  "bplacement", "bplace", "3", "a", "1", "" \
                  "nobexpand", "nobex", "3", "w", "1", "")
        t = t \ ("bexpand", "bex", "3", "w", "1", "" \
                  "width", "width", "3", "a", "1", "" \
                  "height", "height", "3", "a", "1", "" \
                  "nodraw", "nodraw", "3", "w", "1", "" \
                  "draw", "draw", "3", "w", "1", "" \
                  "on", "on", "3", "w", "1", "")
        t = t \ ("off", "off", "3", "w", "1", "" \
                  "tstyle", "tsty", "4", "a", "1", "" \
                  "angle", "angle", "4", "a", "1", "" \
                  "size", "s", "4", "a", "1", "" \
                  "color", "c", "4", "a", "1", "" \
                  "justification", "j", "4", "a", "1", "")
        t = t \ ("alignment", "a", "4", "a", "1", "" \
                  "margin", "m", "4", "a", "1", "" \
                  "linegap", "linegap", "4", "a", "1", "" \
                  "nobox", "nob", "4", "w", "1", "" \
                  "box", "b", "4", "w", "1", "" \
                  "bmargin", "bm", "4", "a", "1", "")
        t = t \ ("placement", "place", "4", "a", "1", "" \
                  "bfcolor", "bfc", "4", "a", "1", "" \
                  "fcolor", "fc", "4", "a", "1", "" \
                  "bcolor", "bc", "4", "a", "1", "" \
                  "blstyle", "blst", "4", "a", "1", "" \
                  "blwidth", "blw", "4", "a", "1", "")
        t = t \ ("blcolor", "blc", "4", "a", "1", "" \
                  "blpattern", "blp", "4", "a", "1", "" \
                  "blalign", "bla", "4", "a", "1", "" \
                  "lstyle", "lst", "4", "a", "1", "" \
                  "lwidth", "lw", "4", "a", "1", "" \
                  "lcolor", "lc", "4", "a", "1", "")
        t = t \ ("lpattern", "lp", "4", "a", "1", "" \
                  "lalign", "la", "4", "a", "1", "" \
                  "orientation", "orient", "4", "a", "1", "")
        // The edge titles are not legend() options: twoway refuses
        // legend(t1title()) .. legend(b2title()), r(198) (WP-43 LT-13).
        t = t \ ("note", "note", "5", "r", "1", "")
        t = t \ ("caption", "cap", "5", "r", "1", "" \
                  "subtitle", "sub", "5", "r", "1", "" \
                  "title", "t", "5", "r", "1", "" \
                  "label", "lab", "6", "r", "1", "" \
                  "lastlabel", "lastlab", "7", "r", "1", "")
    }
    else if (fam == "axlabel") {
        t = t \ ("add", "add", "1", "w", "1", "" \
                  "custom", "custom", "1", "w", "1", "" \
                  "norescale", "norescale", "1", "w", "1", "" \
                  "noticks", "notick", "2", "w", "0", "" \
                  "ticks", "tick", "2", "w", "0", "" \
                  "nolabels", "nolab", "2", "w", "0", "")
        t = t \ ("labels", "labels", "2", "w", "0", "" \
                  "noshowlabels", "noshowlab", "2", "w", "0", "" \
                  "showlabels", "showlab", "2", "w", "0", "" \
                  "novaluelabels", "noval", "2", "w", "0", "" \
                  "valuelabels", "val", "2", "w", "0", "" \
                  "angle", "ang", "2", "a", "0", "")
        t = t \ ("alternate", "alt", "2", "w", "0", "" \
                  "altgap", "altgap", "2", "a", "0", "" \
                  "style", "sty", "2", "a", "0", "" \
                  "tstyle", "tsty", "2", "a", "0", "" \
                  "tlength", "tl", "2", "a", "0", "" \
                  "tposition", "tp", "2", "a", "0", "")
        t = t \ ("labgap", "labgap", "2", "a", "0", "" \
                  "tlstyle", "tlsty", "2", "a", "0", "" \
                  "tlwidth", "tlw", "2", "a", "0", "" \
                  "tlcolor", "tlc", "2", "a", "0", "" \
                  "tlpattern", "tlp", "2", "a", "0", "" \
                  "labstyle", "labsty", "2", "a", "0", "")
        t = t \ ("labsize", "labs", "2", "a", "0", "" \
                  "labcolor", "labc", "2", "a", "0", "" \
                  "labjustification", "labj", "2", "a", "0", "" \
                  "labalignment", "laba", "2", "a", "0", "" \
                  "nopgmgrid", "nopgmgrid", "2", "w", "0", "" \
                  "pgmgrid", "pgmgrid", "2", "w", "0", "")
        t = t \ ("nogrid", "nog", "2", "w", "0", "" \
                  "grid", "g", "2", "w", "0", "" \
                  "gstyle", "gs", "2", "a", "0", "" \
                  "nogextend", "nogex", "2", "w", "0", "" \
                  "gextend", "gex", "2", "w", "0", "" \
                  "nogmin", "nogmin", "2", "w", "0", "")
        t = t \ ("gmin", "gmin", "2", "w", "0", "" \
                  "nogmax", "nogmax", "2", "w", "0", "" \
                  "gmax", "gmax", "2", "w", "0", "" \
                  "glstyle", "gls", "2", "a", "0", "" \
                  "glwidth", "glw", "2", "a", "0", "" \
                  "glcolor", "glc", "2", "a", "0", "")
        t = t \ ("glpattern", "glp", "2", "a", "0", "" \
                  "format", "for", "2", "a", "0", "" \
                  "axis", "ax", "2", "a", "0", "" \
                  "labelminlen", "labelminlen", "2", "a", "0", "I" \
                  "labelkeepleadingzero", "labelkeepleadingzero", "2", "w", "0", "" \
                  "custom", "custom", "2", "w", "0", "")
    }
    else if (fam == "axscale") {
        t = t \ ("nolog", "nolog", "1", "w", "1", "" \
                  "log", "log", "1", "w", "1", "" \
                  "noatanh", "noatanh", "1", "w", "1", "" \
                  "atanh", "atanh", "1", "w", "1", "" \
                  "nologit", "nologit", "1", "w", "1", "" \
                  "logit", "logit", "1", "w", "1", "")
        t = t \ ("nolog1m", "nolog1", "1", "w", "1", "" \
                  "log1m", "log1", "1", "w", "1", "" \
                  "alternate", "alt", "1", "w", "1", "" \
                  "style", "sty", "1", "a", "1", "" \
                  "titlegap", "titleg", "1", "a", "1", "" \
                  "outergap", "outerg", "1", "a", "1", "")
        t = t \ ("noline", "noli", "1", "w", "1", "" \
                  "line", "li", "1", "w", "1", "" \
                  "noextend", "noex", "1", "w", "1", "" \
                  "extend", "ex", "1", "w", "1", "" \
                  "nofextend", "nofex", "1", "w", "1", "" \
                  "fextend", "fex", "1", "w", "1", "")
        t = t \ ("lstyle", "lst", "1", "a", "1", "" \
                  "lcolor", "lc", "1", "a", "1", "" \
                  "lwidth", "lw", "1", "a", "1", "" \
                  "lpattern", "lp", "1", "a", "1", "" \
                  "on", "on", "1", "w", "1", "" \
                  "off", "off", "1", "w", "1", "")
        t = t \ ("nofillspace", "nofill", "1", "w", "1", "" \
                  "fillspace", "fill", "1", "w", "1", "" \
                  "ring", "ring", "1", "a", "1", "R" \
                  "noreverse", "norev", "1", "w", "1", "" \
                  "reverse", "rev", "1", "w", "1", "" \
                  "axis", "ax", "1", "a", "1", "")
        t = t \ ("range", "r", "2", "r", "1", "")
    }
    else if (fam == "clegend") {
        // WP-42 CV-10: twoway's clegend() words at the graph level
        // (clegend_option.sthlp; measured, colorvar_refusal_truth.json
        // K_cleg_*): t1title() .. r2title() and at() are refused there.
        t = t \ ("width", "width", "1", "r", "0", "" \
                  "height", "height", "1", "r", "0", "" \
                  "altaxis", "altaxis", "1", "w", "0", "" \
                  "bmargin", "bm", "1", "r", "0", "" \
                  "title", "ti", "1", "r", "0", "" \
                  "subtitle", "sub", "1", "r", "0", "")
        t = t \ ("note", "note", "1", "r", "0", "" \
                  "caption", "cap", "1", "r", "0", "" \
                  "region", "reg", "1", "r", "0", "" \
                  "off", "off", "1", "w", "0", "" \
                  "on", "on", "1", "w", "0", "" \
                  "position", "pos", "1", "r", "0", "")
        t = t \ ("ring", "ring", "1", "r", "0", "" \
                  "bplacement", "bplace", "1", "r", "0", "")
    }
    else if (fam == "refline") {
        t = t \ ("style", "st", "1", "a", "0", "" \
                  "noextend", "noex", "1", "w", "0", "" \
                  "extend", "ex", "1", "w", "0", "" \
                  "lstyle", "lst", "1", "a", "0", "" \
                  "lcolor", "lc", "1", "a", "0", "" \
                  "lwidth", "lw", "1", "a", "0", "")
        t = t \ ("lpattern", "lp", "1", "a", "0", "" \
                  "lalign", "la", "1", "a", "0", "" \
                  "axis", "ax", "1", "a", "0", "")
    }
    else if (fam == "title") {
        t = t \ ("nospan", "nospan", "1", "w", "1", "" \
                  "span", "span", "1", "w", "1", "" \
                  "prefix", "prefix", "1", "w", "1", "" \
                  "suffix", "suffix", "1", "w", "1", "" \
                  "position", "pos", "1", "a", "1", "" \
                  "ring", "ring", "1", "a", "1", "")
        t = t \ ("style", "sty", "1", "a", "1", "" \
                  "width", "width", "2", "a", "1", "" \
                  "height", "height", "2", "a", "1", "" \
                  "noastextbox", "noast", "2", "w", "1", "" \
                  "nobexpand", "nobex", "2", "w", "1", "" \
                  "astextbox", "ast", "2", "w", "1", "")
        t = t \ ("bexpand", "bex", "2", "w", "1", "" \
                  "tstyle", "tsty", "3", "a", "1", "" \
                  "angle", "angle", "3", "a", "1", "" \
                  "size", "s", "3", "a", "1", "" \
                  "color", "c", "3", "a", "1", "" \
                  "justification", "j", "3", "a", "1", "")
        t = t \ ("alignment", "a", "3", "a", "1", "" \
                  "margin", "m", "3", "a", "1", "" \
                  "linegap", "linegap", "3", "a", "1", "" \
                  "nobox", "nob", "3", "w", "1", "" \
                  "box", "b", "3", "w", "1", "" \
                  "bmargin", "bm", "3", "a", "1", "")
        t = t \ ("placement", "place", "3", "a", "1", "" \
                  "bfcolor", "bfc", "3", "a", "1", "" \
                  "fcolor", "fc", "3", "a", "1", "" \
                  "bcolor", "bc", "3", "a", "1", "" \
                  "blstyle", "blst", "3", "a", "1", "" \
                  "blwidth", "blw", "3", "a", "1", "")
        t = t \ ("blcolor", "blc", "3", "a", "1", "" \
                  "blpattern", "blp", "3", "a", "1", "" \
                  "blalign", "bla", "3", "a", "1", "" \
                  "lstyle", "lst", "3", "a", "1", "" \
                  "lwidth", "lw", "3", "a", "1", "" \
                  "lcolor", "lc", "3", "a", "1", "")
        t = t \ ("lpattern", "lp", "3", "a", "1", "" \
                  "lalign", "la", "3", "a", "1", "" \
                  "orientation", "orient", "3", "a", "1", "")
    }
    else if (fam == "axtitle") {
        t = t \ ("prefix", "prefix", "1", "w", "1", "" \
                  "suffix", "suffix", "1", "w", "1", "" \
                  "axis", "ax", "1", "a", "1", "" \
                  "width", "width", "2", "a", "1", "" \
                  "height", "height", "2", "a", "1", "" \
                  "noastextbox", "noast", "2", "w", "1", "")
        t = t \ ("nobexpand", "nobex", "2", "w", "1", "" \
                  "astextbox", "ast", "2", "w", "1", "" \
                  "bexpand", "bex", "2", "w", "1", "" \
                  "tstyle", "tsty", "3", "a", "1", "" \
                  "angle", "angle", "3", "a", "1", "" \
                  "size", "s", "3", "a", "1", "")
        t = t \ ("color", "c", "3", "a", "1", "" \
                  "justification", "j", "3", "a", "1", "" \
                  "alignment", "a", "3", "a", "1", "" \
                  "margin", "m", "3", "a", "1", "" \
                  "linegap", "linegap", "3", "a", "1", "" \
                  "nobox", "nob", "3", "w", "1", "")
        t = t \ ("box", "b", "3", "w", "1", "" \
                  "bmargin", "bm", "3", "a", "1", "" \
                  "placement", "place", "3", "a", "1", "" \
                  "bfcolor", "bfc", "3", "a", "1", "" \
                  "fcolor", "fc", "3", "a", "1", "" \
                  "bcolor", "bc", "3", "a", "1", "")
        t = t \ ("blstyle", "blst", "3", "a", "1", "" \
                  "blwidth", "blw", "3", "a", "1", "" \
                  "blcolor", "blc", "3", "a", "1", "" \
                  "blpattern", "blp", "3", "a", "1", "" \
                  "blalign", "bla", "3", "a", "1", "" \
                  "lstyle", "lst", "3", "a", "1", "")
        t = t \ ("lwidth", "lw", "3", "a", "1", "" \
                  "lcolor", "lc", "3", "a", "1", "" \
                  "lpattern", "lp", "3", "a", "1", "" \
                  "lalign", "la", "3", "a", "1", "" \
                  "orientation", "orient", "3", "a", "1", "")
    }
    else if (fam == "textbox") {
        t = t \ ("tstyle", "tsty", "1", "a", "1", "" \
                  "bcolor", "bc", "1", "a", "1", "" \
                  "orientation", "orient", "1", "a", "1", "" \
                  "fcolor", "fc", "1", "a", "1", "" \
                  "size", "s", "1", "a", "1", "" \
                  "lstyle", "lst", "1", "a", "1", "")
        t = t \ ("color", "c", "1", "a", "1", "" \
                  "lpattern", "lp", "1", "a", "1", "" \
                  "justification", "j", "1", "a", "1", "" \
                  "lwidth", "lw", "1", "a", "1", "" \
                  "alignment", "a", "1", "a", "1", "" \
                  "lcolor", "lc", "1", "a", "1", "")
        t = t \ ("margin", "m", "1", "a", "1", "" \
                  "lalign", "la", "1", "a", "1", "" \
                  "linegap", "linegap", "1", "a", "1", "" \
                  "width", "width", "1", "a", "1", "" \
                  "height", "height", "1", "a", "1", "" \
                  "bmargin", "bm", "1", "a", "1", "")
        t = t \ ("box", "b", "1", "a", "1", "" \
                  "nobox", "nob", "1", "a", "1", "" \
                  "bexpand", "bex", "1", "a", "1", "" \
                  "placement", "place", "1", "a", "1", "" \
                  "position", "pos", "1", "a", "1", "" \
                  "ring", "ring", "1", "a", "1", "")
        t = t \ ("span", "span", "1", "a", "1", "" \
                  "prefix", "prefix", "1", "a", "1", "" \
                  "suffix", "suffix", "1", "a", "1", "" \
                  "axis", "ax", "1", "a", "1", "" \
                  "angle", "angle", "1", "a", "1", "" \
                  "bfcolor", "bfc", "1", "a", "1", "")
        t = t \ ("blstyle", "blst", "1", "a", "1", "" \
                  "blwidth", "blw", "1", "a", "1", "" \
                  "blcolor", "blc", "1", "a", "1", "" \
                  "blpattern", "blp", "1", "a", "1", "" \
                  "blalign", "bla", "1", "a", "1", "" \
                  "nobexpand", "nobex", "1", "a", "1", "")
        t = t \ ("astextbox", "ast", "1", "a", "1", "" \
                  "noastextbox", "noast", "1", "a", "1", "" \
                  "nospan", "nospan", "1", "a", "1", "")
    }
    if (fam == "region") {
        // _fr_area_parse_and_log.ado:33-43 (WP-30 P1.20a): one unstarred
        // stage, in declaration order; twin of _dash_region_table().
        t = t \ ("style", "sty", "1", "a", "0", "" \
                  "istyle", "isty", "1", "a", "0", "" \
                  "lstyle", "ls", "1", "a", "0", "" \
                  "ilstyle", "ils", "1", "a", "0", "" \
                  "lcolor", "lc", "1", "a", "0", "" \
                  "ilcolor", "ilc", "1", "a", "0", "" \
                  "lwidth", "lw", "1", "a", "0", "" \
                  "ilwidth", "ilw", "1", "a", "0", "")
        t = t \ ("lpattern", "lp", "1", "a", "0", "" \
                  "ilpattern", "ilp", "1", "a", "0", "" \
                  "lalign", "la", "1", "a", "0", "" \
                  "ilalign", "ila", "1", "a", "0", "" \
                  "shadestyle", "shades", "1", "a", "0", "" \
                  "ishadestyle", "ishades", "1", "a", "0", "" \
                  "fcolor", "fc", "1", "a", "0", "" \
                  "ifcolor", "ifc", "1", "a", "0", "")
        t = t \ ("color", "c", "1", "a", "0", "" \
                  "icolor", "ic", "1", "a", "0", "" \
                  "intensity", "inten", "1", "a", "0", "" \
                  "iintensity", "iinten", "1", "a", "0", "" \
                  "margin", "m", "1", "a", "0", "" \
                  "marginonly", "marginonly", "1", "w", "0", "")
    }
    return(t)
}

// _dash_so_canon(name, fam) -- the full name typed name abbreviates in
// family fam, or "": lower case only, from a row's minimum to its full
// name, the first row in table order winning.
string scalar _dash_so_canon(string scalar name, string scalar fam)
{
    string matrix t
    string scalar nm
    real scalar   i

    nm = strtrim(name)
    if (nm == "" | nm != strlower(nm)) return("")
    t = _dash_so_rows(fam)
    for (i = 1; i <= rows(t); i++) {
        if (strlen(nm) >= strlen(t[i, 2]) & strlen(nm) <= strlen(t[i, 1]) &
            substr(t[i, 1], 1, strlen(nm)) == nm) return(t[i, 1])
    }
    return("")
}

// _dash_ring_ok(v) -- how title(), subtitle(), note() and caption() take
// ring(v) (WP-43 LT-14; title_box_truth.json ring_w_<w>, ring_x): 1 for a
// real number or one of the words inside and outside (dash_render.py's
// _DASH_RING_WORDS, the same two), drawn; -1 for another lowercase
// abbreviation of inside or outside, which twoway refuses with no note;
// 0 for anything else, refused after twoway's two gridringstyle notes.
real scalar _dash_ring_ok(string scalar v)
{
    string scalar    t
    string rowvector words

    words = ("inside", "outside")
    t = strtrim(v)
    if (_dash_so_isnum(t, 0)) return(1)
    if (anyof(words, t)) return(1)
    if (t != "" & (strpos("inside", t) == 1 | strpos("outside", t) == 1)) {
        return(-1)
    }
    return(0)
}

// _dash_so_isnum(s, isint) -- 1 when s, stripped, is twoway's integer
// literal [+-]?digits (isint) or real literal [+-]?(d+.?d*|.d+)([eE][+-]?d+)?
// and nothing else.  Byte by byte.
real scalar _dash_so_isnum(string scalar s, real scalar isint)
{
    string scalar t, c
    real scalar   i, n, nd, nf, dot

    t = strtrim(s)
    n = strlen(t)
    i = 1
    if (n == 0) return(0)
    c = substr(t, 1, 1)
    if (c == "+" | c == "-") i = 2
    nd  = 0
    nf  = 0
    dot = 0
    while (i <= n) {
        c = substr(t, i, 1)
        if (c >= "0" & c <= "9") {
            if (dot) nf++
            else nd++
        }
        else if (c == "." & !dot & !isint) dot = 1
        else break
        i++
    }
    if (nd + nf == 0) return(0)
    if (i > n) return(1)
    if (isint) return(0)
    c = substr(t, i, 1)
    if (c != "e" & c != "E") return(0)
    i++
    if (i <= n) {
        c = substr(t, i, 1)
        if (c == "+" | c == "-") i++
    }
    if (i > n) return(0)
    for (; i <= n; i++) {
        c = substr(t, i, 1)
        if (c < "0" | c > "9") return(0)
    }
    return(1)
}

// _dash_so_resolve(toks, cid, fam, names, msg, at) -- twoway's reading of
// one option's sub-option words: toks every copy's words in command
// order, cid each word's copy.  names is set to each word's full name or
// "".  Returns 198 with msg twoway's message ("option po() not allowed",
// "option labs incorrectly specified") and at the word's index for the
// first problem, else 0.  Each stage, in order, names the unnamed words of
// each copy; a starred stage passes what it cannot take on, an unstarred
// one refuses it; what no stage named is refused.  Linear in words times
// rows.
real scalar _dash_so_resolve(string rowvector toks, real rowvector cid,
                             string scalar fam, string rowvector names,
                             string scalar msg, real scalar at)
{
    string matrix    t
    string rowvector nm
    string scalar    taken, bad, arg
    real rowvector   paren
    real scalar      i, j, s, smax, star, row, p, c, n

    t     = _dash_so_rows(fam)
    n     = cols(toks)
    names = J(1, n, "")
    nm    = J(1, n, "")
    paren = J(1, n, 0)
    msg   = ""
    at    = 0
    for (i = 1; i <= n; i++) {
        p = strpos(toks[i], "(")
        nm[i]    = strtrim(p ? substr(toks[i], 1, p - 1) : toks[i])
        paren[i] = (p > 0)
    }
    smax = 0
    for (j = 1; j <= rows(t); j++) smax = max((smax, strtoreal(t[j, 3])))
    for (s = 1; s <= smax; s++) {
        star = -1
        for (j = 1; j <= rows(t); j++) {
            if (strtoreal(t[j, 3]) == s) {
                star = (t[j, 5] == "1")
                break
            }
        }
        if (star < 0) continue
        taken = " "
        c     = .
        for (i = 1; i <= n; i++) {
            if (cid[i] != c) {
                c     = cid[i]
                taken = " "
            }
            if (names[i] != "") continue
            row = 0
            if (nm[i] != "" & nm[i] == strlower(nm[i])) {
                for (j = 1; j <= rows(t); j++) {
                    if (strtoreal(t[j, 3]) != s) continue
                    if (strlen(nm[i]) >= strlen(t[j, 2]) &
                        strlen(nm[i]) <= strlen(t[j, 1]) &
                        substr(t[j, 1], 1, strlen(nm[i])) == nm[i]) {
                        row = j
                        break
                    }
                }
            }
            bad = ""
            if (!row) bad = "none"
            else {
                if (strpos(taken, " " + t[row, 1] + ":" + t[row, 4] + " ") &
                    (t[row, 4] == "a" | (star & t[row, 4] == "w"))) {
                    bad = "taken"
                }
                else if ((t[row, 4] == "w") == paren[i]) bad = "form"
                else if (t[row, 6] == "R" | t[row, 6] == "I") {
                    arg = _dash_rep_value(toks[i])
                    if (substr(toks[i], strlen(toks[i]), 1) != ")") {
                        arg = substr(toks[i], strpos(toks[i], "(") + 1, .)
                    }
                    if (!_dash_so_isnum(arg, t[row, 6] == "I")) bad = "form"
                }
            }
            if (bad == "") {
                names[i] = t[row, 1]
                taken = taken + t[row, 1] + ":" + t[row, 4] + " "
                continue
            }
            if (star) continue
            if (at == 0) {
                at  = i
                msg = "option " + nm[i] + (paren[i] ? "()" : "") +
                      (bad == "form" ? " incorrectly specified" :
                       " not allowed")
            }
        }
        if (at) return(198)
    }
    for (i = 1; i <= n; i++) {
        if (names[i] == "") {
            at  = i
            msg = "option " + nm[i] + (paren[i] ? "()" : "") + " not allowed"
            return(198)
        }
    }
    return(0)
}

// _dash_so_family(key) -- the sub-option table a merge key reads: legend()
// "legend", an axis label or tick list "axlabel", an axis scale
// "axscale", a title "textbox", plotregion() and graphregion() "region"
// (WP-30 P1.20a); "" for by(), text() and lines.
string scalar _dash_so_family(string scalar key)
{
    string scalar cat

    if (_dash_rep_bare(key) == "legend") return("legend")
    if (anyof(("plotregion", "graphregion"), _dash_rep_bare(key))) return("region")
    cat = _dash_rep_cat(key)
    if (cat == "L") return("axlabel")
    if (cat == "S") return("axscale")
    if (cat == "T" | cat == "TA") return("textbox")
    return("")
}

// _dash_so_unsafe(s) -- 1 when s holds a backtick, $, a quote, a backslash
// or a byte below 32: a value never put to -numlist-.
real scalar _dash_so_unsafe(string scalar s)
{
    real scalar i, b

    for (i = 1; i <= strlen(s); i++) {
        b = ascii(substr(s, i, 1))
        if (b < 32 | b == 96 | b == 36 | b == 39 | b == 34 | b == 92) return(1)
    }
    return(0)
}

// _dash_subreq_clear(), _dash_subreq_add(opts, seg), _dash_subreq_check(kind)
// and _dash_subreq_accept() -- twoway's refusals of the sub-options of
// legend(), zlabel() and the titles (WP-30 P1.19).  _dash_subreq_add
// records, from the RAW option text (called by _dash_axreq_add, with its
// arguments), one row per option in the external _dash_subreq: kind
// ("legend", "zlabel", "title:<name>" or "axtitle:<name>"), seg, place and
// the sub-option words.  _dash_subreq_check resolves them with twoway's
// tables and refuses the first problem with twoway's words through
// _dash_say, r(198); a cols()/rows()/holes() value it hands back (-1, the
// caller's locals _so_name, _so_value and _so_kind) for dash.ado's
// _dash_subopt_check to put to -numlist-, which then accepts it
// (_dash_subreq_accept) and checks again.  The record is cleared at the
// start of every graph command and after every check or refusal, so no
// typed text is kept.
void _dash_subreq_clear()
{
    external string matrix _dash_subreq
    external real rowvector _dash_subreq_ok
    external real scalar    _dash_subreq_last

    _dash_subreq      = J(0, 4, "")
    _dash_subreq_ok   = J(1, 0, .)
    _dash_subreq_last = 0
}

void _dash_subreq_add(string scalar opts, real scalar seg)
{
    external string matrix _dash_subreq
    string rowvector toks, tnames, tmins
    string scalar    nm, v, body, sub, b2, s2, kind
    real scalar      i, j, k

    toks = _dash_rep_toks(opts, 0)
    if (cols(toks) == 0) return
    tnames = ("title", "subtitle", "note", "caption", "t1title", "t2title",
              "b1title", "b2title", "l1title", "l2title", "r1title",
              "r2title", "xtitle", "ytitle", "xtitle2", "ytitle2", "ztitle")
    tmins  = ("ti", "sub", "note", "cap", "t1", "t2", "b1", "b2", "l1",
              "l2", "r1", "r2", "xti", "yti", "xtitle2", "ytitle2", "zti")
    if (rows(_dash_subreq) == 0 | cols(_dash_subreq) != 4) {
        _dash_subreq = J(0, 4, "")
    }
    for (i = 1; i <= cols(toks); i++) {
        if (!strpos(toks[i], "(")) continue
        nm = _dash_rep_optname(toks[i])
        if (nm == "" | nm != strlower(nm)) continue
        v  = _dash_rep_value(toks[i])
        kind = ""
        if (strlen(nm) >= 3 & substr("legend", 1, strlen(nm)) == nm) {
            kind = "legend"
            sub  = v
        }
        else if ((strlen(nm) >= 4 & substr("zlabel", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 4 & substr("ztick", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 3 & substr("zmlabel", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 3 & substr("zmtick", 1, strlen(nm)) == nm)) {
            // WP-42 AX-12: the z tick family's sub-options are an axis
            // label's too (colorvar_refusal_truth.json K_ztic_subopt:
            // ztick(5000, bogus) is "option bogus not allowed", r(198)).
            kind = (substr(nm, 1, 2) == "zl" ? "zlabel" :
                    (substr(nm, 1, 2) == "zt" ? "ztick" :
                     (substr(nm, 1, 3) == "zml" ? "zmlabel" : "zmtick")))
            sub  = ""
            if (_dash_rep_split(v, body, sub)) {
                if (_dash_rep_split(sub, b2, s2)) sub = b2
            }
        }
        else if ((strlen(nm) >= 4 & substr("clegend", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 4 & substr("plegend", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 3 & substr("zscale", 1, strlen(nm)) == nm)) {
            // WP-42 CV-10: the colour key's options and zscale(), checked
            // by kind (clegend, plegend, zscale) with twoway's tables.
            kind = (substr(nm, 1, 1) == "c" ? "clegend" :
                    (substr(nm, 1, 1) == "p" ? "plegend" : "zscale"))
            sub  = v
        }
        else if ((strlen(nm) >= 6 & substr("graphregion", 1, strlen(nm)) == nm) |
                 (strlen(nm) >= 5 & substr("plotregion", 1, strlen(nm)) == nm)) {
            // A region's whole value (WP-30 P1.20a): graphr() and plotr()
            // are the minimums dash.sthlp states.
            kind = "region:" + (substr(nm, 1, 1) == "g" ? "graphregion" : "plotregion")
            sub  = v
        }
        else {
            k = 0
            for (j = 1; j <= cols(tnames); j++) {
                if (strlen(nm) >= strlen(tmins[j]) &
                    strlen(nm) <= strlen(tnames[j]) &
                    substr(tnames[j], 1, strlen(nm)) == nm) {
                    k = j
                    break
                }
            }
            if (k) {
                kind = (anyof(("xtitle", "ytitle", "xtitle2", "ytitle2",
                               "ztitle"), tnames[k]) ? "axtitle:" : "title:") +
                       tnames[k]
                sub = ""
                (void) _dash_rep_split(v, body, sub)
            }
        }
        if (kind == "" | strtrim(sub) == "") continue
        _dash_subreq = _dash_subreq \ (kind, strofreal(seg), strofreal(i), sub)
    }
}

// _dash_subreq_toks(kind, toks, cid) -- every recorded copy of kind (an
// exact kind, or every title/axtitle kind when kind is "title:" or
// "axtitle:" and the next name) in (seg, place) order, as one word list
// and each word's copy number.
void _dash_subreq_toks(string scalar kind, string rowvector toks,
                       real rowvector cid)
{
    external string matrix _dash_subreq
    string rowvector w
    real colvector   o
    real scalar      i, c

    toks = J(1, 0, "")
    cid  = J(1, 0, .)
    if (rows(_dash_subreq) == 0) return
    o = order(strtoreal(_dash_subreq[., (2, 3)]), (1, 2))
    c = 0
    for (i = 1; i <= rows(o); i++) {
        if (_dash_subreq[o[i], 1] != kind) continue
        // A title's empty slots -- ytitle(A,,) -- are no words, as twoway
        // ignores them (WP-29 P0.4).
        w = _dash_rep_toks(_dash_subreq[o[i], 4], kind != "legend")
        if (cols(w) == 0) continue
        c++
        toks = toks, w
        cid  = cid, J(1, cols(w), c)
    }
}

// _dash_subreq_label(w, opt) -- twoway's refusal of label()/lastlabel()'s
// key word w (one pair of quotes stripped), or "".
string scalar _dash_subreq_label(string scalar w, string scalar opt)
{
    string scalar t, d
    real scalar   i, nz

    t = w
    if (strlen(t) >= 2 & substr(t, 1, 1) == char(34) &
        substr(t, strlen(t), 1) == char(34)) t = substr(t, 2, strlen(t) - 2)
    if (t == "") return("")
    d = t
    if (substr(d, 1, 1) == "+" | substr(d, 1, 1) == "-") d = substr(d, 2, .)
    if (d == "" | !_dash_is_digits(d, .)) {
        return(t + " not an integer in option " + opt + "()")
    }
    nz = 0
    for (i = 1; i <= strlen(d); i++) if (substr(d, i, 1) != "0") nz = 1
    if (substr(t, 1, 1) == "-" | !nz) return("legend.labels[" + t + "] invalid name")
    return("")
}

real scalar _dash_subreq_check(string scalar kind)
{
    external string matrix  _dash_subreq
    external real rowvector _dash_subreq_ok
    external real scalar    _dash_subreq_last
    string rowvector toks, names, w, kinds
    string scalar    msg, f, arg, lastpos, lastring, lastorder, m, fam
    real rowvector   cid
    real colvector   o
    real scalar      rc, at, i, j, k, c, q, hasp, hass, edge

    if (rows(_dash_subreq) == 0 | cols(_dash_subreq) != 4) {
        _dash_subreq_clear()
        return(0)
    }
    if (kind == "legend") {
        _dash_subreq_toks("legend", toks, cid)
        if (cols(toks) == 0) return(0)
        rc = _dash_so_resolve(toks, cid, "legend", names, msg, at)
        if (cols(_dash_subreq_ok) == 0) _dash_subreq_ok = J(1, 0, .)
        // 1. Values, in twoway's order: per copy, holes() rows() cols()
        //    as ParseLogOpts declares them; then every label(), then
        //    every lastlabel().
        for (c = 1; c <= max(cid); c++) {
            for (k = 1; k <= 3; k++) {
                f = (k == 1 ? "holes" : (k == 2 ? "rows" : "cols"))
                for (i = 1; i <= cols(toks); i++) {
                    if (cid[i] != c | names[i] != f) continue
                    if (anyof(_dash_subreq_ok, i)) continue
                    arg = strtrim(_dash_rep_value(toks[i]))
                    if (arg == "") continue
                    _dash_subreq_last = i
                    st_local("_so_name", f)
                    st_local("_so_value", arg)
                    st_local("_so_kind", f == "holes" ? "NL" : "N1")
                    return(-1)
                }
            }
        }
        for (k = 1; k <= 2; k++) {
            f = (k == 1 ? "label" : "lastlabel")
            for (i = 1; i <= cols(toks); i++) {
                if (names[i] != f) continue
                w = _dash_rep_toks(_dash_rep_value(toks[i]), 0)
                m = (cols(w) ? _dash_subreq_label(w[1], f) : "")
                if (m != "") {
                    _dash_say("err", "", m, "")
                    _dash_subreq_clear()
                    return(198)
                }
            }
        }
        // 2. The leftover.  A bare top/bottom/left/right is left to
        //    _dash_check_legend, which adds the position() hint.
        if (rc) {
            if (anyof(("top", "bottom", "left", "right"), toks[at])) {
                _dash_subreq_drop("legend")
                return(0)
            }
            _dash_say("err", "", msg, "")
            _dash_subreq_clear()
            return(198)
        }
        // 2b. The words inside region() and the legend's own titles, read
        //     with twoway's region and title tables (WP-31 D16): they
        //     reached the renderer unread.
        msg = _dash_subreq_nested(toks, names)
        if (msg != "") {
            _dash_say("err", "", msg, "")
            _dash_subreq_clear()
            return(198)
        }
        // 3. twoway's notes, once each.
        lastpos   = ""
        lastring  = ""
        lastorder = ""
        hasp      = 0
        for (i = 1; i <= cols(toks); i++) {
            if (names[i] == "position") lastpos   = strtrim(_dash_rep_value(toks[i]))
            if (names[i] == "ring")     lastring  = strtrim(_dash_rep_value(toks[i]))
            if (names[i] == "order") {
                lastorder = _dash_rep_value(toks[i])
                hasp = 1
            }
        }
        // position() and ring() are noted only where twoway's clockdir and
        // gridringstyle do not read them (WP-45 ST-3, ST-4: top, b, in, o
        // are read; style_words_truth.json).
        if (lastpos != "" & _dash_style_word("clockdir", lastpos) == "") {
            _dash_note("named style ", lastpos,
                       " not found in class clockdir, default attributes used")
        }
        // A lowercase abbreviation of inside or outside is drawn with no
        // note (WP-43 LT-9; title_box_truth.json leg_ring_w_<w>).
        if (lastring != "" & _dash_style_word("gridringstyle", lastring) == ""
            & _dash_ring_ok(lastring) != 1) {
            _dash_note("named style ", lastring,
                       " not found in class gridringstyle, default attributes used")
            _dash_note("", "gridringstyle",
                       " not found in scheme, default attributes used")
        }
        if (hasp) {
            w = _dash_rep_toks(lastorder, 0)
            for (j = 1; j <= cols(w); j++) {
                q = ascii(substr(w[j], 1, 1))
                if (q == 34 | q == 96 | w[j] == "-") continue
                if (_dash_so_isnum(w[j], 1)) continue
                _dash_note("", w[j], " not an integer, option order() ignored")
                break
            }
        }
        _dash_subreq_drop("legend")
        return(0)
    }
    if (kind == "region") {
        // WP-30 P1.20a: every graphregion() copy, then every plotregion()
        // copy, in (seg, place) order, each read alone, as twoway's
        // twowaygraph_g.class:183 and :456 call the region parser.
        o = order(strtoreal(_dash_subreq[., (2, 3)]), (1, 2))
        for (k = 1; k <= 2; k++) {
            f = (k == 1 ? "region:graphregion" : "region:plotregion")
            for (q = 1; q <= rows(o); q++) {
                if (_dash_subreq[o[q], 1] != f) continue
                m = _dash_subreq_region(_dash_subreq[o[q], 4])
                if (m != "") {
                    _dash_say("err", "", m, "")
                    _dash_subreq_clear()
                    return(198)
                }
            }
        }
        // WP-31 D11: a margin() text twoway fails on, when the region's
        // log is run, after every copy has parsed.
        for (k = 1; k <= 2; k++) {
            f = (k == 1 ? "region:graphregion" : "region:plotregion")
            for (q = 1; q <= rows(o); q++) {
                if (_dash_subreq[o[q], 1] != f) continue
                rc = _dash_subreq_margin(_dash_subreq[o[q], 4], msg)
                if (rc) {
                    _dash_say("err", "", msg, "")
                    _dash_subreq_clear()
                    return(rc)
                }
            }
        }
        _dash_subreq_drop("region:graphregion")
        _dash_subreq_drop("region:plotregion")
        return(0)
    }
    if (anyof(("zlabel", "ztick", "zmlabel", "zmtick"), kind)) {
        for (i = 1; i <= rows(_dash_subreq); i++) {
            if (_dash_subreq[i, 1] != kind) continue
            toks = _dash_rep_toks(_dash_subreq[i, 4], 1)
            if (cols(toks) == 0) continue
            if (_dash_so_resolve(toks, J(1, cols(toks), 1), "axlabel",
                                 names, msg, at)) {
                _dash_say("err", "", msg, "")
                _dash_subreq_clear()
                return(198)
            }
        }
        _dash_subreq_drop(kind)
        return(0)
    }
    if (kind == "clegend" | kind == "plegend" | kind == "zscale") {
        // WP-42 CV-10: clegend() with clegend's table, plegend() with
        // legend's, zscale() with the axis scale's, every copy together
        // as twoway merges them; the words inside region() and the titles
        // with their own tables (_dash_subreq_nested).
        _dash_subreq_toks(kind, toks, cid)
        if (cols(toks)) {
            fam = (kind == "plegend" ? "legend" : (kind == "zscale" ? "axscale" : "clegend"))
            if (_dash_so_resolve(toks, cid, fam, names, msg, at)) {
                _dash_say("err", "", msg, "")
                _dash_subreq_clear()
                return(198)
            }
            if (kind != "zscale") {
                msg = _dash_subreq_nested(toks, names)
                if (msg != "") {
                    _dash_say("err", "", msg, "")
                    _dash_subreq_clear()
                    return(198)
                }
            }
        }
        _dash_subreq_drop(kind)
        return(0)
    }
    if (kind == "title") {
        kinds = J(1, 0, "")
        for (i = 1; i <= rows(_dash_subreq); i++) {
            if (substr(_dash_subreq[i, 1], 1, 6) != "title:" &
                substr(_dash_subreq[i, 1], 1, 8) != "axtitle:") continue
            if (!anyof(kinds, _dash_subreq[i, 1])) kinds = kinds, _dash_subreq[i, 1]
        }
        for (k = 1; k <= cols(kinds); k++) {
            _dash_subreq_toks(kinds[k], toks, cid)
            if (cols(toks) == 0) continue
            fam = (substr(kinds[k], 1, 8) == "axtitle:" ? "axtitle" : "title")
            if (fam == "title") {
                // twoway takes the suffix and prints this line, rc 0
                // (WP-31 D16; tabs_legend_edges_truth.json title.*).
                for (c = 1; c <= max(cid); c++) {
                    hasp = 0
                    hass = 0
                    for (i = 1; i <= cols(toks); i++) {
                        if (cid[i] != c) continue
                        if (_dash_so_canon(toks[i], "title") == "prefix") hasp = 1
                        if (_dash_so_canon(toks[i], "title") == "suffix") hass = 1
                    }
                    if (hasp & hass) {
                        _dash_say("txt", "option prefix ignored, may not be combined with suffix", "", "")
                    }
                }
            }
            if (fam == "axtitle") {
                for (c = 1; c <= max(cid); c++) {
                    hasp = 0
                    hass = 0
                    for (i = 1; i <= cols(toks); i++) {
                        if (cid[i] != c) continue
                        if (_dash_so_canon(toks[i], "axtitle") == "prefix") hasp = 1
                        if (_dash_so_canon(toks[i], "axtitle") == "suffix") hass = 1
                    }
                    if (hasp & hass) {
                        _dash_say("err", "options prefix and suffix may not be combined", "", "")
                        _dash_subreq_clear()
                        return(198)
                    }
                }
            }
            if (_dash_so_resolve(toks, cid, fam, names, msg, at)) {
                _dash_say("err", "", msg, "")
                _dash_subreq_clear()
                return(198)
            }
            // A ring() twoway refuses (WP-43 LT-14; title_box_truth.json
            // ring_x, ring_w_<w>, e_ring_*): on title(), subtitle(), note()
            // and caption() a word other than inside and outside, after
            // twoway's two notes unless it abbreviates one of them; on an
            // edge title every word, with no note.
            if (fam == "title") {
                edge = ustrregexm(kinds[k], "^title:[tblr][12]title$")
                for (i = 1; i <= cols(toks); i++) {
                    if (names[i] != "ring") continue
                    arg = strtrim(_dash_rep_value(toks[i]))
                    q = _dash_ring_ok(arg)
                    if (edge & q == 1 & !_dash_so_isnum(arg, 0)) q = -1
                    if (edge & q == 0) q = -1
                    if (q == 1) continue
                    if (q == 0) {
                        _dash_note("named style ", arg,
                                   " not found in class gridringstyle, default attributes used")
                        _dash_note("", "gridringstyle",
                                   " not found in scheme, default attributes used")
                    }
                    _dash_say("err", "option ring() incorrectly specified", "", "")
                    _dash_subreq_clear()
                    return(198)
                }
                // position() and orientation() of title(), subtitle(),
                // note() and caption(): a word clockdir or tb_orientstyle
                // does not read gets twoway's note (WP-45 ST-11;
                // style_words_truth.json clockdir/tb_orientstyle title rows).
                for (i = 1; i <= cols(toks); i++) {
                    if (edge) break
                    arg = strtrim(_dash_rep_value(toks[i]))
                    if (arg == "") continue
                    if (names[i] == "position" &
                        _dash_style_word("clockdir", arg) == "") {
                        _dash_note("named style ", arg,
                                   " not found in class clockdir, default attributes used")
                    }
                    if (names[i] == "orientation" &
                        _dash_style_word("tb_orientstyle", arg) == "") {
                        _dash_note("named style ", arg,
                                   " not found in class tb_orientstyle, default attributes used")
                    }
                }
            }
        }
        _dash_subreq_clear()
        return(0)
    }
    return(0)
}

// _dash_bare_string_refusal(cmd) -- twoway's refusal of a quoted string
// standing alone among a command's options, or "" (WP-31 D16b).  A string
// is bare when it opens at an option list's own level: after a plot's or
// the graph's comma, not inside an option's parentheses and not before
// the comma (scatteri's labels).  twoway refuses every one, r(198), in
// words that follow how its parser pairs the quotes and parentheses it
// then sees (tabs_legend_edges_truth.json bare.*, 28 probes): an even
// number of bare strings, or one among the graph's options after
// parenthesised plots, is "invalid syntax"; otherwise one written beside
// ||, in a plot group followed by another group or by the graph's
// options, or beside an option holding a quoted value is "parentheses do
// not balance"; otherwise "quotes unbalanced".  dash's catch-all kept the
// string and named it in the note.
string scalar _dash_bare_string_refusal(string scalar cmd)
{
    real scalar   n, i, nxt, in_dq, in_cq, depth, inopt0, inopt1, ngroups,
                  bars, nbare, ing, inp, gopts, qparen, optbase, c, opening
    string scalar prev

    n = strlen(cmd)
    prev = ""
    in_dq = 0
    in_cq = 0
    depth = 0
    inopt0 = 0
    inopt1 = 0
    ngroups = 0
    bars = 0
    nbare = 0
    ing = 0
    inp = 0
    gopts = 0
    qparen = 0
    i = 1
    while (i <= n) {
        c = ascii(substr(cmd, i, 1))
        opening = (c == 34 | (c == 96 & i < n & ascii(substr(cmd, i + 1, 1)) == 34))
        if (opening) {
            // Where the string opens: an option list's own level is depth
            // 0 after a top-level comma, or depth 1 inside a plot group
            // after the group's comma.
            optbase = (depth == 0 & inopt0) | (depth == 1 & ngroups & inopt1 & !inopt0)
            if (optbase) {
                nbare++
                if (depth == 0 & ngroups) ing = 1
                if (depth == 1) inp = 1
            }
            else if (depth > (inopt0 ? 0 : (ngroups ? 1 : 0))) qparen = 1
            while (i <= n) {
                nxt = _dash_quote_step(cmd, n, i, in_dq, in_cq)
                if (!nxt) nxt = i + 1
                i = nxt
                if (!in_dq & !in_cq) break
            }
            prev = char(34)
            continue
        }
        if (c == 40) {
            // A plot group opens at depth 0 before the graph's comma, at
            // the start or after a group or ||; inlist( in a qualifier is
            // a function's parentheses.
            if (depth == 0 & !inopt0 & (prev == "" | prev == ")" | prev == "|")) {
                ngroups++
                inopt1 = 0
            }
            depth++
        }
        else if (c == 41) {
            if (depth > 0) depth--
        }
        else if (c == 44) {
            if (depth == 0) {
                inopt0 = 1
                if (ngroups) gopts = 1
            }
            else if (depth == 1 & ngroups & !inopt0) inopt1 = 1
        }
        else if (c == 124 & depth == 0 & i < n & ascii(substr(cmd, i + 1, 1)) == 124) {
            bars = 1
            inopt0 = 0
            prev = "|"
            i = i + 2
            continue
        }
        if (c != 32 & c != 9) prev = char(c)
        i++
    }
    if (nbare == 0) return("")
    if (mod(nbare, 2) == 0 | ing) return("invalid syntax")
    if (bars | (inp & (ngroups > 1 | gopts)) | qparen) return("parentheses do not balance")
    return("quotes unbalanced")
}

// _dash_stray_quote_refusal(cmd) -- twoway's refusal of option text
// holding a stray "', as "<rc>|<first line>", or "" (WP-43 LT-24,
// maintainer ruling P4-5).  A stray is a double quote followed by an
// apostrophe -- the close of a compound quote -- met outside compound
// quotes inside an option frame: a parenthesis that follows a name
// [A-Za-z_][A-Za-z0-9_]* at a level in options (after a comma at that
// level; || and the close of a group parenthesis leave them), or any
// parenthesis inside one.  A stray outside every option frame -- in an
// if or in qualifier, a weight -- is not read here: dash keeps it as
// typed (P4-5).  twoway's answer, measured on the 57 probes of
// test/fixtures/quote_truth.json: when the stray's " closes a plain
// string, r(132) "too many ')' or ']'" with ) right after the
// apostrophe, else r(198) "parentheses do not balance"; otherwise the
// first character outside quotes after the apostrophe (read with the
// same quote rules) decides -- a blank, tab, comma, =, { or } r(109)
// "type mismatch", ( or [ r(132) "too few ')' or ']'", ) or ] r(132)
// "too many ')' or ']'" -- and with none r(100) ") required", as for
// title("'90s", size(large)), whose comma lies inside the string the
// stray's apostrophe reopens.  The command is read by value.
string scalar _dash_stray_quote_refusal(string scalar cmd)
{
    real scalar    n, i, j, b, c, nx, d, q, k, nopt, isname, at, closes, nxt
    real colvector fopt, fgrp, finopt
    string scalar  ch, SET_MISMATCH, SET_FEW, SET_MANY

    // The characters after the stray that decide twoway's answer.
    SET_MISMATCH = " " + char(9) + ",={}"
    SET_FEW      = "(["
    SET_MANY     = ")]"

    n = strlen(cmd)
    fopt   = J(n + 1, 1, 0)
    fgrp   = J(n + 1, 1, 0)
    finopt = J(n + 1, 1, 0)
    k = 1
    nopt = 0
    d = 0
    q = 0
    at = 0
    closes = 0
    i = 1
    while (i <= n) {
        c = ascii(substr(cmd, i, 1))
        nx = (i < n ? ascii(substr(cmd, i + 1, 1)) : -1)
        if (d) {
            if (c == 96 & nx == 34) {
                d++
                i = i + 2
                continue
            }
            if (c == 34 & nx == 39) {
                d--
                i = i + 2
                continue
            }
            i++
            continue
        }
        if (q) {
            if (c == 34) {
                if (nx == 39 & nopt) {
                    at = i
                    closes = 1
                    break
                }
                q = 0
            }
            i++
            continue
        }
        if (c == 96 & nx == 34) {
            d = 1
            i = i + 2
            continue
        }
        if (c == 34) {
            if (nx == 39 & nopt) {
                at = i
                break
            }
            q = 1
            i++
            continue
        }
        if (c == 40) {
            // A name right before the parenthesis: letters, digits and
            // underscores, not starting with a digit.
            j = i - 1
            while (j >= 1) {
                b = ascii(substr(cmd, j, 1))
                if ((b >= 48 & b <= 57) | (b >= 65 & b <= 90) | (b >= 97 & b <= 122) | b == 95) j--
                else break
            }
            isname = 0
            if (j < i - 1) {
                b = ascii(substr(cmd, j + 1, 1))
                isname = !(b >= 48 & b <= 57)
            }
            k++
            fopt[k] = (finopt[k - 1] & isname) | (nopt > 0)
            fgrp[k] = !isname
            finopt[k] = 0
            nopt = nopt + fopt[k]
        }
        else if (c == 41) {
            if (k > 1) {
                nopt = nopt - fopt[k]
                if (fgrp[k]) finopt[k - 1] = 0
                k--
            }
        }
        else if (c == 44) finopt[k] = 1
        else if (c == 124 & nx == 124) {
            finopt[k] = 0
            i = i + 2
            continue
        }
        i++
    }
    if (!at) return("")
    if (closes) {
        if (substr(cmd, at + 2, 1) == ")") return("132|too many ')' or ']'")
        return("198|parentheses do not balance")
    }
    q = 0
    d = 0
    i = at + 2
    while (i <= n) {
        nxt = _dash_quote_step(cmd, n, i, q, d)
        if (nxt) {
            i = nxt
            continue
        }
        ch = substr(cmd, i, 1)
        if (strpos(SET_MISMATCH, ch)) return("109|type mismatch")
        if (strpos(SET_FEW, ch)) return("132|too few ')' or ']'")
        if (strpos(SET_MANY, ch)) return("132|too many ')' or ']'")
        i++
    }
    return("100|) required")
}

// _dash_subreq_nested(toks, names) -- twoway's refusal of a word inside a
// legend's region() (the region table) or its title(), subtitle(), note(),
// caption() or t1title() ... r2title() (the title table, after the text's
// comma), or "" (WP-31 D16).  toks are the legend's words and names their
// canonical names (_dash_so_resolve).  Measured: legend(region(xx)) and
// legend(title("T", xx)) are "option xx not allowed", r(198); a style
// name it does not know is drawn with a note (the renderer's).
string scalar _dash_subreq_nested(string rowvector toks, string rowvector names)
{
    string rowvector w, nm
    string scalar    v, body, sub, msg
    real scalar      i, at

    for (i = 1; i <= cols(toks); i++) {
        if (i > cols(names)) break
        if (!strpos(toks[i], "(")) continue
        v = _dash_rep_value(toks[i])
        if (names[i] == "region") {
            w = _dash_rep_toks(v, 0)
            if (cols(w) == 0) continue
            if (_dash_so_resolve(w, J(1, cols(w), 1), "region", nm, msg, at)) return(msg)
        }
        else if (anyof(("title", "subtitle", "note", "caption", "t1title",
                        "t2title", "b1title", "b2title", "l1title",
                        "l2title", "r1title", "r2title"), names[i])) {
            sub = ""
            if (!_dash_rep_split(v, body, sub)) continue
            w = _dash_rep_toks(sub, 1)
            if (cols(w) == 0) continue
            if (_dash_so_resolve(w, J(1, cols(w), 1), "title", nm, msg, at)) return(msg)
        }
    }
    return("")
}

// _dash_legend_first_refusal(text) -- twoway's refusal of legend() text
// whose first word twoway cannot read comes before a bare top, bottom,
// left or right, or "" (WP-31 D16).  twoway reads the words left to right:
// legend(po(9) top) is "option po() not allowed", which _dash_check_legend
// named top for.  Where the keyword comes first, or there is none, "":
// _dash_check_legend and _dash_subreq_check answer as before.
string scalar _dash_legend_first_refusal(string scalar text)
{
    string rowvector toks, names, kw
    string scalar    msg
    real scalar      at, j

    toks = _dash_rep_toks(text, 0)
    if (cols(toks) == 0) return("")
    kw = ("top", "bottom", "left", "right")
    if (!_dash_so_resolve(toks, J(1, cols(toks), 1), "legend", names, msg, at)) return("")
    if (anyof(kw, toks[at])) return("")
    for (j = at + 1; j <= cols(toks); j++) {
        if (anyof(kw, toks[j])) return(msg)
    }
    return("")
}

// _dash_subreq_region(v) -- twoway's refusal of one region copy's value v,
// or "" (WP-30 P1.20a): a word after a top-level comma is "invalid
// '<word>'" (blanks after it are ignored); then the words are read with
// twoway's region table (_dash_so_resolve: an unknown, capitalised or
// too-short name, or one given twice, "option c() not allowed"); then a
// word option given twice, "option marginonly not allowed".
string scalar _dash_subreq_region(string scalar v)
{
    string rowvector w, names
    string scalar    body, sub, msg
    real scalar      at, i, j, p

    body = v
    if (_dash_rep_split(v, body, sub)) {
        w = _dash_rep_toks(sub, 1)
        if (cols(w)) {
            p = strpos(w[1], "(")
            return("invalid '" + (p ? substr(w[1], 1, p - 1) : w[1]) + "'")
        }
    }
    w = _dash_rep_toks(body, 0)
    if (cols(w) == 0) return("")
    if (_dash_so_resolve(w, J(1, cols(w), 1), "region", names, msg, at)) {
        return(msg)
    }
    for (i = 1; i <= cols(w); i++) {
        if (names[i] != "marginonly") continue
        for (j = i + 1; j <= cols(w); j++) {
            if (names[j] == "marginonly") return("option " + w[j] + " not allowed")
        }
    }
    return("")
}

// _dash_margin_term_rc(t, msg) -- twoway's return code for margin(t), 7
// with its line in msg, or 0 (WP-31 D11, measured in
// test/fixtures/region_remainder_truth.json refusals.* and terms.*).
// margin.class's setstyle takes a style name when t holds -pt -in -cm or
// -rs, starts with the word scheme, or is one word with no + - =;
// otherwise it hides the units rs pt in cm as w x y z, splits t at blanks
// and at each of l r t b + -, and reads the token after + or - as a
// number: when it is not one, its part before x, y or z (that letter
// itself when it leads) must be, or "'<part>' found where number
// expected", r(7) (allsides-ms fails on ms, l+abc on a, l+inf on y).
real scalar _dash_margin_term_rc(string scalar t, string scalar msg)
{
    string rowvector w
    string scalar    s, c, tok, num
    real scalar      i, op, p

    msg = ""
    s = strtrim(t)
    if (s == "") return(0)
    if (strpos(s, "-pt") | strpos(s, "-in") | strpos(s, "-cm") |
        strpos(s, "-rs")) return(0)
    w = tokens(s)
    if (cols(w) == 0) return(0)
    if (w[1] == "scheme") return(0)
    if (cols(w) == 1 & !strpos(s, "+") & !strpos(s, "-") & !strpos(s, "=")) {
        return(0)
    }
    s = subinstr(s, "rs", "w")
    s = subinstr(s, "pt", "x")
    s = subinstr(s, "in", "y")
    s = subinstr(s, "cm", "z")
    op  = 0
    tok = ""
    for (i = 1; i <= strlen(s) + 1; i++) {
        c = (i <= strlen(s) ? substr(s, i, 1) : " ")
        if (!anyof((" ", "l", "r", "t", "b", "+", "-", char(9)), c)) {
            tok = tok + c
            continue
        }
        if (tok != "") {
            if (tok == "=") op = 0
            else {
                if (op & !_dash_margin_isnum(tok)) {
                    p = 0
                    for (p = 1; p <= strlen(tok); p++) {
                        if (anyof(("x", "y", "z"), substr(tok, p, 1))) break
                    }
                    num = (p == 1 ? substr(tok, 1, 1) : substr(tok, 1, p - 1))
                    if (!_dash_margin_isnum(num)) {
                        msg = "'" + num + "' found where number expected"
                        return(7)
                    }
                }
                op = 0
            }
            tok = ""
        }
        if (c == "+" | c == "-") op = 1
    }
    return(0)
}

// _dash_margin_isnum(s) -- 1 when s is a number as -confirm number- takes
// one inside margin.class (digits, one point, an exponent; no sign, the
// signs being parse characters there).
real scalar _dash_margin_isnum(string scalar s)
{
    return(ustrregexm(s, "^([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][+]?[0-9]+)?$"))
}

// _dash_subreq_margin(v, msg) -- twoway's return code for one region
// copy's margin() texts, read in order (_dash_margin_term_rc), its line
// in msg; 0 when every one parses (WP-31 D11).
real scalar _dash_subreq_margin(string scalar v, string scalar msg)
{
    string rowvector w, names
    string scalar    body, sub, m
    real scalar      at, i, rc

    msg  = ""
    body = v
    (void) _dash_rep_split(v, body, sub)
    w = _dash_rep_toks(body, 0)
    if (cols(w) == 0) return(0)
    if (_dash_so_resolve(w, J(1, cols(w), 1), "region", names, m, at)) {
        return(0)
    }
    for (i = 1; i <= cols(w); i++) {
        if (names[i] != "margin") continue
        rc = _dash_margin_term_rc(_dash_rep_value(w[i]), msg)
        if (rc) return(rc)
    }
    return(0)
}

// _dash_subreq_drop(kind) -- the record less its rows of kind, once that
// kind is checked; the accepted values with it.
void _dash_subreq_drop(string scalar kind)
{
    external string matrix  _dash_subreq
    external real rowvector _dash_subreq_ok
    real colvector keep

    _dash_subreq_ok = J(1, 0, .)
    if (rows(_dash_subreq) == 0) return
    keep = (_dash_subreq[., 1] :!= kind)
    if (any(keep)) _dash_subreq = select(_dash_subreq, keep)
    else _dash_subreq = J(0, 4, "")
}

// _dash_subreq_accept() -- the value _dash_subreq_check last handed back
// passed -numlist-: it is not handed back again.
void _dash_subreq_accept()
{
    external real rowvector _dash_subreq_ok
    external real scalar    _dash_subreq_last

    if (_dash_subreq_last > 0) _dash_subreq_ok = _dash_subreq_ok, _dash_subreq_last
    _dash_subreq_last = 0
}

// _dash_rep_subkey(tok, cat, full) -- which sub-option a word sets, for keeping
// the last of each: its full name (full, twoway's reading; WP-30 P1.19) or
// else its typed name in lower case, a noX taken as X (grid and nogrid,
// box and nobox are one setting), on and off as one, and label(# ...) and
// lastlabel(# ...) keyed by their number.  cols and rows are keys of their
// own; _dash_rep_subs lets rows() beat cols().
string scalar _dash_rep_subkey(string scalar tok, string scalar cat,
                               string scalar full)
{
    string scalar nm, v
    real scalar   p

    p  = strpos(tok, "(")
    nm = (full != "" ? full : strlower(strtrim(p ? substr(tok, 1, p - 1) : tok)))
    if (strlen(nm) > 2 & substr(nm, 1, 2) == "no" & nm != "note") nm = substr(nm, 3, .)
    if (nm == "on" | nm == "off") nm = "on|off"
    if ((nm == "label" | nm == "lastlabel") & cat == "I" & p) {
        v = strtrim(_dash_rep_value(tok))
        nm = nm + " " + (strpos(v, " ") ? substr(v, 1, strpos(v, " ") - 1) : v)
    }
    return(nm)
}

// _dash_rep_subs(s1, s2, cat, drop, key) -- two sub-option lists as one: every
// word of s1 then s2, keeping only the last word of each setting
// (_dash_rep_subkey), in the order the kept words stand, less the words
// listed in drop (suffix, prefix, add: merging instructions, spent here).
// On an axis scale ("S") every range() is one range(), the union of the
// ranges written, as twoway draws xscale(range(0 8000)) xscale(range(1000
// 6000)) over 0 to 8000; when one is not numbers (a tscale() date), their
// values joined in one range() (WP-30 P1.6).
//
// For legend(), the axis labels and ticks, the scales and the titles
// (_dash_so_family(key); WP-30 P1.19) each side is first read as twoway
// reads it (_dash_so_resolve, s1 copy 1 and s2 copy 2), so a word is keyed
// by its full name: lab(1 "AA") and label(2 "BB") are two labels, c(2) and
// cols(1) one setting.  On each side of legend() and an axis label a word
// beats its no form, and on beats off, as twoway's code order has it;
// rows() beats every cols() in legend(); and a word whose full name is not
// the one its spelling alone gives (the second c() of cols(1) c(red) is
// color()) is written under its full name, so the merged text reads the
// same.
string scalar _dash_rep_subs(string scalar s1, string scalar s2,
                             string scalar cat, string rowvector drop,
                             | string scalar key)
{
    string rowvector w, keys, full, rw1, rw2, rn1, rn2
    string scalar    out, k, fam, msg, nm, rv
    real scalar      i, j, keep, lo, hi, v, nr, rng, ok, n1, at, p, hasrows
    real rowvector   nums, cid, alive

    // A region (WP-30 P1.20a): each copy read alone, then copy 2 applied
    // to copy 1 as twoway's parser applies it (_dash_rep_region).
    fam = (args() >= 5 ? _dash_so_family(key) : "")
    if (fam == "region") {
        rw1 = _dash_rep_toks(s1, 1)
        rw2 = _dash_rep_toks(s2, 1)
        (void) _dash_so_resolve(rw1, J(1, cols(rw1), 1), "region", rn1, msg, at)
        (void) _dash_so_resolve(rw2, J(1, cols(rw2), 1), "region", rn2, msg, at)
        return(_dash_rep_region(rw1, rn1, rw2, rn2))
    }
    n1 = cols(_dash_rep_toks(s1, 1))
    w = _dash_rep_toks(s1, 1), _dash_rep_toks(s2, 1)
    keys  = J(1, cols(w), "")
    full  = J(1, cols(w), "")
    alive = J(1, cols(w), 1)
    if (fam != "" & cols(w)) {
        cid = J(1, n1, 1), J(1, cols(w) - n1, 2)
        (void) _dash_so_resolve(w, cid, fam, full, msg, at)
        if (fam == "legend" | fam == "axlabel") {
            for (i = 1; i <= cols(w); i++) {
                nm = full[i]
                if (nm == "") continue
                for (j = 1; j <= cols(w); j++) {
                    if (cid[j] != cid[i] | j == i) continue
                    if ((strlen(nm) > 2 & substr(nm, 1, 2) == "no" &
                         full[j] == substr(nm, 3, .)) |
                        (nm == "off" & full[j] == "on")) {
                        alive[i] = 0
                        break
                    }
                }
            }
        }
    }
    for (i = 1; i <= cols(w); i++) keys[i] = _dash_rep_subkey(w[i], cat, full[i])
    lo  = .
    hi  = .
    nr  = 0
    ok  = 1
    rng = 0
    if (cat == "S") {
        for (i = 1; i <= cols(w); i++) {
            if (keys[i] != "range" | !strpos(w[i], "(")) continue
            nr++
            rng = i
            nums = strtoreal(tokens(_dash_rep_value(w[i])))
            if (cols(nums) == 0 | missing(nums)) ok = 0
            else {
                lo = (lo >= . ? min(nums) : min((lo, min(nums))))
                hi = (hi >= . ? max(nums) : max((hi, max(nums))))
            }
        }
    }
    hasrows = 0
    if (fam == "legend") {
        for (i = 1; i <= cols(w); i++) if (alive[i] & full[i] == "rows") hasrows = 1
    }
    out = ""
    for (i = 1; i <= cols(w); i++) {
        if (!alive[i]) continue
        if (anyof(drop, strlower(w[i]))) continue
        if (hasrows & full[i] == "cols") continue
        keep = 1
        for (j = i + 1; j <= cols(w); j++) {
            if (alive[j] & keys[j] == keys[i]) {
                keep = 0
                break
            }
        }
        if (!keep) continue
        if (full[i] != "") {
            p = strpos(w[i], "(")
            if (_dash_so_canon(p ? substr(w[i], 1, p - 1) : w[i], fam) != full[i]) {
                out = out + (out == "" ? "" : " ") + full[i] +
                      (p ? substr(w[i], p, .) : "")
                continue
            }
        }
        if (cat == "S" & i == rng & nr > 1 & ok) {
            out = out + (out == "" ? "" : " ") + "range(" +
                  strtrim(strofreal(lo, "%21.0g")) + " " +
                  strtrim(strofreal(hi, "%21.0g")) + ")"
            continue
        }
        // A range() that is no number -- tscale(range(1999m1))
        // tscale(range(2006m1)), dates read later by _dash_taxis_fold --
        // keeps every copy's values, in order, in the one range() kept,
        // so their union is taken once they are numbers (WP-30 P1.6).
        if (cat == "S" & i == rng & nr > 1 & !ok) {
            rv = ""
            for (j = 1; j <= cols(w); j++) {
                if (keys[j] != "range" | !strpos(w[j], "(")) continue
                rv = rv + (rv == "" ? "" : " ") + strtrim(_dash_rep_value(w[j]))
            }
            out = out + (out == "" ? "" : " ") + "range(" + rv + ")"
            continue
        }
        out = out + (out == "" ? "" : " ") + w[i]
    }
    return(out)
}

// _dash_rep_region(w1, n1, w2, n2) -- two copies of plotregion() or
// graphregion() as one (WP-30 P1.20a): w1/w2 each copy's words, n1/n2
// their full names ("" for a word twoway refuses, which keeps its typed
// form and its typed name).  twoway's _fr_area_parse_and_log.ado applies
// each copy to the result of the one before (.style.editstyle), so a name
// in copy 2 drops what it overrides in copy 1 -- style() everything but
// margin(); lstyle() the outline; shadestyle() the fill; color() color,
// fcolor and lcolor; fcolor() and lcolor() their own name, leaving copy
// 1's color() the other half (written fcolor()/lcolor(), or dropped when
// copy 1 sets that half itself); the rest their own name -- and every
// margin() is kept, in order, for section 47.  The i* twins follow the same
// rules among themselves.  Returns copy 1's survivors then copy 2, each as
// full(arg).  Byte loops, no regular expression.
string scalar _dash_rep_region(string rowvector w1, string rowvector n1,
                               string rowvector w2, string rowvector n2)
{
    string rowvector a, an, drop, w2b, n2b
    string scalar    out, nm, base, pre, rw, tn
    real rowvector   alive
    real scalar      i, j, k, has

    // WP-31 D11: a copy with marginonly posts only its margin() edits
    // (_fr_area_parse_and_log.ado), so it is cut to them here, per copy,
    // before the merge; the merged text never carries marginonly.
    a  = _dash_rep_region_mo(w1, n1, 1)
    an = _dash_rep_region_mo(w1, n1, 0)
    w2b = _dash_rep_region_mo(w2, n2, 1)
    n2b = _dash_rep_region_mo(w2, n2, 0)
    alive = J(1, cols(a), 1)
    for (j = 1; j <= cols(w2b); j++) {
        nm = n2b[j]
        if (nm == "margin" | nm == "imargin") continue
        if (nm == "") {
            tn = _dash_rep_optname(w2b[j])
            for (i = 1; i <= cols(a); i++) {
                if (an[i] == "" & _dash_rep_optname(a[i]) == tn) alive[i] = 0
            }
            continue
        }
        pre  = ""
        base = nm
        if (substr(nm, 1, 1) == "i" & nm != "intensity") {
            pre  = "i"
            base = substr(nm, 2, .)
        }
        rw   = ""
        drop = (base)
        if (base == "style") {
            drop = ("style", "lstyle", "lcolor", "lwidth", "lpattern",
                    "lalign", "shadestyle", "color", "fcolor", "intensity")
        }
        else if (base == "lstyle") {
            drop = ("lstyle", "lcolor", "lwidth", "lpattern", "lalign")
            rw   = "fcolor"
        }
        else if (base == "shadestyle") {
            drop = ("shadestyle", "fcolor", "intensity")
            rw   = "lcolor"
        }
        else if (base == "color") drop = ("color", "fcolor", "lcolor")
        else if (base == "fcolor") rw = "lcolor"
        else if (base == "lcolor") rw = "fcolor"
        for (k = 1; k <= cols(drop); k++) drop[k] = pre + drop[k]
        for (i = 1; i <= cols(a); i++) {
            if (alive[i] & anyof(drop, an[i])) alive[i] = 0
        }
        if (rw == "") continue
        for (i = 1; i <= cols(a); i++) {
            if (!alive[i] | an[i] != pre + "color") continue
            has = 0
            for (k = 1; k <= cols(a); k++) {
                if (alive[k] & an[k] == pre + rw) has = 1
            }
            if (has) alive[i] = 0
            else {
                a[i]  = pre + rw + "(" + _dash_rep_value(a[i]) + ")"
                an[i] = pre + rw
            }
        }
    }
    out = ""
    for (i = 1; i <= cols(a); i++) {
        if (!alive[i]) continue
        out = out + (out == "" ? "" : " ") + _dash_rep_region_word(a[i], an[i])
    }
    for (j = 1; j <= cols(w2b); j++) {
        out = out + (out == "" ? "" : " ") + _dash_rep_region_word(w2b[j], n2b[j])
    }
    return(out)
}

// _dash_rep_region_mo(w, n, words) -- one region copy's words (words 1)
// or their full names (words 0), cut to its margin() words when the copy
// holds marginonly (WP-31 D11); else as given.
string rowvector _dash_rep_region_mo(string rowvector w, string rowvector n,
                                     real scalar words)
{
    real rowvector keep
    real scalar    i

    if (!anyof(n, "marginonly")) return(words ? w : n)
    keep = J(1, cols(n), 0)
    for (i = 1; i <= cols(n); i++) keep[i] = (n[i] == "margin")
    if (!any(keep)) return(J(1, 0, ""))
    return(select(words ? w : n, keep))
}

// _dash_rep_region_word(w, full) -- a region word as full(arg), or as
// typed when twoway gave it no full name; marginonly bare.
string scalar _dash_rep_region_word(string scalar w, string scalar full)
{
    if (full == "") return(w)
    if (!strpos(w, "(")) return(full)
    return(full + substr(w, strpos(w, "("), .))
}

// _dash_rep_merge(key, v1, v2) -- the value twoway draws for option key
// written first with value v1 and then with v2 (_dash_rep_cat says how).
// An axis-label option (cat L) keeps add as twoway merges it (WP-30
// P1.18b, test/fixtures/axis_add_truth.json): ylabel(25, add)
// ylabel(35, add) is 25 35, add (both held add); ylabel(25)
// ylabel(35, add) is 25 35 (appended, add spent); ylabel(25, add)
// ylabel(35) is 35; ylabel(25, nolabels) ylabel(35, add) is 25 35,
// nolabels; and a copy with no values keeps the earlier copy's add
// (a01: ylabel(25, add) ylabel(, nolabels) is 25, nolabels add).
string scalar _dash_rep_merge(string scalar key, string scalar v1,
                              string scalar v2)
{
    string scalar    cat, b1, s1, b2, s2, body, sub
    string rowvector w2, drop
    real scalar      c1, c2, has2, suf, pre, add, a1, keep, lines

    cat = _dash_rep_cat(key)
    // An axis title (TA) merges as a title (T), its suffix/prefix copy
    // on a line of its own (WP-44 MS-13).
    lines = (cat == "TA")
    if (lines) cat = "T"
    if (cat == "F") return(strtrim(v1) != "" ? v1 : v2)
    if (cat == "R" | strtrim(v1) == "") return(v2)
    if (strtrim(v2) == "") return(v1)
    // Each copy kept apart by a record separator; _dash_at_lex splits
    // only outside quotes (WP-30 P1.10).
    if (cat == "A") return(v1 + char(30) + v2)
    if (cat == "H") return(strtrim(v1) + " " + strtrim(v2))
    if (cat == "X") return(v1 + ", " + v2)
    if (cat == "S") {
        return(_dash_rep_alt(v1, v2, _dash_rep_subs(v1, v2, cat, J(1, 0, ""), key)))
    }
    if (cat == "I") {
        return(_dash_rep_subs(v1, v2, cat, J(1, 0, ""), key))
    }
    c1 = _dash_rep_split(v1, b1, s1)
    c2 = _dash_rep_split(v2, b2, s2)
    w2   = strlower(_dash_rep_toks(s2, 1))
    has2 = (strtrim(b2) != "")
    suf  = (cat == "T" & anyof(w2, "suffix"))
    pre  = (cat == "T" & anyof(w2, "prefix"))
    add  = (cat == "L" & anyof(w2, "add"))
    drop = ("suffix", "prefix")
    if (cat == "L") drop = ("add")
    if (suf & has2 & lines)      body = _dash_rep_lines(b1, b2)
    else if (pre & has2 & lines) body = _dash_rep_lines(b2, b1)
    else if (suf & has2)  body = strtrim(b1) + " " + strtrim(b2)
    else if (pre & has2)  body = strtrim(b2) + " " + strtrim(b1)
    else if (add & has2)  body = strtrim(b1) + " " + strtrim(b2)
    else                  body = (has2 ? strtrim(b2) : strtrim(b1))
    sub = _dash_rep_subs(s1, s2, cat, drop, key)
    if (cat == "L") {
        a1   = anyof(strlower(_dash_rep_toks(s1, 1)), "add")
        keep = (has2 ? (add & a1) : a1)
        if (keep) sub = sub + (sub != "" ? " " : "") + "add"
    }
    return(body + (sub != "" ? ", " + sub : ""))
}

// _dash_rep_lines(a, b) -- the bodies a and b as two lines of one title
// (WP-44 MS-13): each body not already a run of quoted strings (its
// first non-blank character a double quote or a backtick) is wrapped in
// compound quotes, so _parse_textbox_opt reads a line per body; joined
// by one blank.
string scalar _dash_rep_lines(string scalar a, string scalar b)
{
    string scalar x, y

    x = strtrim(a)
    y = strtrim(b)
    if (!anyof((char(34), char(96)), substr(x, 1, 1))) {
        x = char(96) + char(34) + x + char(34) + char(39)
    }
    if (!anyof((char(34), char(96)), substr(y, 1, 1))) {
        y = char(96) + char(34) + y + char(34) + char(39)
    }
    return(x + " " + y)
}

// _dash_rep_alt(v1, v2, merged) -- merged with alt as twoway reads two
// scale copies (WP-31 D7; measured, test/fixtures/axis_look_truth.json
// sc_alt2): each copy's alt toggles the side, so the merged value keeps
// alt only when one of v1 and v2 holds it.  Linear in the words.
string scalar _dash_rep_alt(string scalar v1, string scalar v2,
                            string scalar merged)
{
    string rowvector w
    string scalar    out, nm
    real scalar      a1, a2, i

    a1 = _dash_rep_has_alt(v1)
    a2 = _dash_rep_has_alt(v2)
    if (!a1 & !a2) return(merged)
    w = _dash_rep_toks(merged, 0)
    out = ""
    for (i = 1; i <= cols(w); i++) {
        nm = strlower(w[i])
        if (!strpos(nm, "(") & _dash_so_canon(nm, "axscale") == "alternate") continue
        out = out + (out == "" ? "" : " ") + w[i]
    }
    if (a1 != a2) out = out + (out == "" ? "" : " ") + "alt"
    return(out)
}

// _dash_rep_has_alt(v) -- 1 when the scale value v holds alt.
real scalar _dash_rep_has_alt(string scalar v)
{
    string rowvector w
    real scalar      i
    w = _dash_rep_toks(v, 1)
    for (i = 1; i <= cols(w); i++) {
        if (!strpos(w[i], "(") &
            _dash_so_canon(strlower(w[i]), "axscale") == "alternate") return(1)
    }
    return(0)
}

// _dash_rep_merge_locals(key, m1, m2, out) -- _dash_rep_merge on the
// caller's locals m1 and m2, read by value, into its local out.
void _dash_rep_merge_locals(string scalar key, string scalar m1,
                            string scalar m2, string scalar out)
{
    st_local(out, _dash_rep_merge(key, st_local(m1), st_local(m2)))
}

// ==== text() and ttext() (WP-30 P1.10) ===================================
// twoway draws each copy of text(y x "line" ... [, sub-options]) as text
// boxes at data points (twowaygraph_g.class ParseAndLogText and
// _parse_log_1textbox, StataNow 19.5; test/fixtures/added_text_truth.json).
// _dash_rep_merge keeps repeated copies apart with char(30); these
// functions split them, read each copy's points and lines by value, and
// write the records dash.ado puts in the graph's options.  Nothing here
// runs a copy's text: every token is read as data, numbers through a
// strict literal, date literals (ttext()) only through
// _dash_tdate_value's gate (WP-30 P1.6).  Each scan reads the bytes once,
// so 100,000 copies parse in linear time.

// _dash_at_lex(raw, st, ln, kd, cp, os, ol, nt) -- raw read once, byte by
// byte, as gettoken reads a text() copy.  Copies end at char(30); in each,
// the text before the first comma outside quotes and parentheses is
// tokens -- blank-separated words, or one simple "..." or compound
// string, quotes kept -- and the rest, to the copy's end, its sub-options.
// Sets by reference: per token its start st, length ln, kind kd (1 a
// word, 2 a quoted string) and copy cp; per copy the start os and length
// ol of its sub-options (ol 0 when none).  Returns the number of copies.
// A char(30) inside a quoted string is the string's own; one string
// opened and never closed runs to the copy's end.  Linear in the bytes.
real scalar _dash_at_lex(string scalar raw, real colvector st,
                         real colvector ln, real colvector kd,
                         real colvector cp, real colvector os,
                         real colvector ol, real scalar nt)
{
    real rowvector b
    real scalar    i, j, n, k, depth, par, inopt, open, q

    b  = ascii(raw)
    n  = cols(b)
    st = J(n + 1, 1, 0)
    ln = st
    kd = st
    cp = st
    os = st
    ol = st
    nt = 0
    k  = 1
    inopt = 0
    par   = 0
    open  = 0
    i     = 1
    while (i <= n) {
        q = 0
        if (b[i] == 96 & i < n) q = (b[i + 1] == 34) * 2
        else if (b[i] == 34) q = 1
        if (q) {
            // A quoted string: skip to its close, nested pairs counted.
            j = i + q
            if (q == 2) {
                depth = 1
                while (j <= n) {
                    if (b[j] == 96 & j < n) {
                        if (b[j + 1] == 34) {
                            depth++
                            j = j + 2
                            continue
                        }
                    }
                    if (b[j] == 34 & j < n) {
                        if (b[j + 1] == 39) {
                            depth--
                            j = j + 2
                            if (!depth) break
                            continue
                        }
                    }
                    j++
                }
            }
            else {
                while (j <= n) {
                    if (b[j] == 34) break
                    j++
                }
                j++
            }
            if (j > n + 1) j = n + 1
            if (!inopt) {
                open = 0
                nt++
                st[nt] = i
                ln[nt] = j - i
                kd[nt] = 2
                cp[nt] = k
            }
            i = j
            continue
        }
        if (b[i] == 30) {
            if (inopt) ol[k] = i - os[k]
            open  = 0
            inopt = 0
            par   = 0
            k++
        }
        else if (inopt) {
        }
        else if (b[i] == 32 | b[i] == 9) open = 0
        else if (b[i] == 44 & !par) {
            open  = 0
            inopt = 1
            os[k] = i + 1
        }
        else {
            if (b[i] == 40) par++
            else if (b[i] == 41 & par) par--
            if (open) ln[nt] = ln[nt] + 1
            else {
                open = 1
                nt++
                st[nt] = i
                ln[nt] = 1
                kd[nt] = 1
                cp[nt] = k
            }
        }
        i++
    }
    if (inopt) ol[k] = n + 1 - os[k]
    return(k)
}

// _dash_at_unq(tok, q) -- tok less one pair of enclosing quotes, compound
// or simple, as gettoken reads it; q set to 1 when it had them.
string scalar _dash_at_unq(string scalar tok, real scalar q)
{
    real scalar n

    n = strlen(tok)
    q = 1
    if (n >= 4 & substr(tok, 1, 2) == char(96) + char(34) &
        substr(tok, n - 1, 2) == char(34) + char(39)) {
        return(substr(tok, 3, n - 4))
    }
    if (n >= 2 & substr(tok, 1, 1) == char(34) & substr(tok, n, 1) == char(34)) {
        return(substr(tok, 2, n - 2))
    }
    q = 0
    return(tok)
}

// _dash_at_isnum(tok) -- 1 when tok is a number as twoway's numlist reads
// a point: an optional sign, digits with at most one point, an optional
// exponent, and a value Stata can hold (1e400 is not; 3e3 is); else 0.
// ".", "1+1", "a" and an empty token are not.
real scalar _dash_at_isnum(string scalar tok)
{
    real rowvector b

    if (tok == "" | strpos(tok, char(10)) | strpos(tok, char(13))) return(0)
    // Digits alone, the common case, without the regular expression.
    b = ascii(tok)
    if (cols(b) <= 15) {
        if (all(b :>= 48 :& b :<= 57)) return(1)
    }
    if (!ustrregexm(tok, "^[+-]?([0-9]+[.]?[0-9]*|[.][0-9]+)([eE][+-]?[0-9]+)?$")) return(0)
    return(strtoreal(tok) < .)
}

// _dash_at_parse(raw, datesok) -- every copy of raw read as twoway reads
// it (_dash_at_lex): y x, then its quoted lines, and the next bare token
// is the next point's y.  A point is two numbers (_dash_at_isnum), or
// with datesok (ttext()) a number y and an x holding no parenthesis,
// converted later (_dash_at_dates).  Kept in two Mata externals, read by
// _dash_at_copy and _dash_at_records: _dash_at_C, per copy its
// sub-options, its state (0 no point, 1 every point valid, 2 its first
// point invalid, 3 a later one) and twoway's words for an invalid point
// ("invalid point, <x> <y>"); _dash_at_R, one row per point with a line
// that is not empty: y, x, the lines (a JSON array of escaped strings),
// its copy, and "1" when x is a date literal to convert.  Sets the
// caller's locals _at_k (copies) and _at_n (records).  Returns 0, or 198 when a line its globals expand (_dash_at_globals) passes 4,000 bytes.  Reads
// and writes by value only; 100,000 one-point copies take well under a
// second (AT-04b).
real scalar _dash_at_parse(string scalar raw, real scalar datesok)
{
    external string matrix _dash_at_R, _dash_at_C
    real colvector st, ln, kd, cp, os, ol
    real rowvector bb
    string scalar  y, x, line, js, bare, ks, g
    real scalar    nk, k, j, nt, n, state, pts, any, isd, q

    nk = _dash_at_lex(raw, st, ln, kd, cp, os, ol, nt)
    _dash_at_C = J(nk, 3, "")
    _dash_at_R = J(floor(nt / 3) + 1, 5, "")
    n  = 0
    j  = 1
    for (k = 1; k <= nk; k++) {
        ks = strofreal(k)
        if (ol[k]) _dash_at_C[k, 1] = substr(raw, os[k], ol[k])
        y = ""
        x = ""
        if (cp[j] == k) {
            y = substr(raw, st[j], ln[j])
            if (kd[j] == 2) y = _dash_at_unq(y, q)
            j++
        }
        if (cp[j] == k) {
            x = substr(raw, st[j], ln[j])
            if (kd[j] == 2) x = _dash_at_unq(x, q)
            j++
        }
        state = 0
        pts   = 0
        while (y != "") {
            pts++
            isd = 0
            if (!(_dash_at_isnum(y) & _dash_at_isnum(x))) {
                if (datesok & _dash_at_isnum(y) & x != "" &
                    !strpos(x, "(") & !strpos(x, ")") & !strpos(x, " ")) {
                    isd = 1
                }
                else {
                    state = (pts == 1 ? 2 : 3)
                    _dash_at_C[k, 3] = "invalid point, " + x + " " + y
                    break
                }
            }
            js   = ""
            any  = 0
            bare = ""
            while (cp[j] == k) {
                if (kd[j] != 2) {
                    bare = substr(raw, st[j], ln[j])
                    j++
                    break
                }
                line = _dash_at_unq(substr(raw, st[j], ln[j]), q)
                j++
                // A global the line names, as twoway expands it (WP-31
                // D13), by text: an expansion past 4,000 bytes is refused.
                if (strpos(line, "$")) {
                    // A copy: _dash_at_globals rewrites its argument in
                    // place, so passing line itself made the two equal and
                    // the bound never held (WP-31 D13b).
                    g = _dash_at_globals(line + "", 1)
                    if (g != line & strlen(g) > 4000) {
                        st_local("_at_k", "0")
                        st_local("_at_n", "0")
                        return(198)
                    }
                    line = g
                }
                // {ccl name} as twoway's graph text draws it (WP-31 E9).
                line = _dash_gt_ccl(line)
                // _dash_json_escape() only where a byte needs it.
                bb = ascii(line)
                if (cols(bb)) {
                    if (any(bb :< 32 :| bb :== 34 :| bb :== 36 :| bb :== 39 :|
                            bb :== 92 :| bb :== 96)) line = _dash_json_escape(line)
                    any = 1
                }
                js = js + (js != "" ? "," : "") + char(34) + line + char(34)
            }
            if (any) {
                n++
                _dash_at_R[n, 1] = y
                _dash_at_R[n, 2] = x
                _dash_at_R[n, 3] = "[" + js + "]"
                _dash_at_R[n, 4] = ks
                if (isd) _dash_at_R[n, 5] = "1"
            }
            y = bare
            x = ""
            if (y != "" & cp[j] == k) {
                x = substr(raw, st[j], ln[j])
                if (kd[j] == 2) x = _dash_at_unq(x, q)
                j++
            }
        }
        // The copy's tokens left after an invalid point are skipped.
        while (cp[j] == k) j++
        if (state == 0 & pts) state = 1
        _dash_at_C[k, 2] = strofreal(state)
    }
    _dash_at_R = (n ? _dash_at_R[1..n, .] : J(0, 5, ""))
    st_local("_at_k", strofreal(nk))
    st_local("_at_n", strofreal(n))
    return(0)
}

// _dash_at_copy(k) -- copy k of the last _dash_at_parse into the caller's
// locals _at_o (its sub-options), _at_s (its state) and _at_e (twoway's
// words for its invalid point, or "").
void _dash_at_copy(real scalar k)
{
    external string matrix _dash_at_C

    st_local("_at_o", _dash_at_C[k, 1])
    st_local("_at_s", _dash_at_C[k, 2])
    st_local("_at_e", _dash_at_C[k, 3])
}

// _dash_at_dates(u1, u2) -- each record of the last _dash_at_parse whose x
// is a date literal (ttext()) converted in the unit of its x axis, u1 or
// u2 (_dash_taxis_unit; the axis is the caller's local _at_xa<copy>), by
// S51's gated converter (_dash_tdate_value), the token read as data and
// never run.  Returns 0, or 198 with the token in the caller's local
// _at_err when it is no date of that unit, or a missing value, which
// twoway refuses: "<x> is not a number".
real scalar _dash_at_dates(string scalar u1, string scalar u2)
{
    external string matrix _dash_at_R
    real scalar    i, rc, val

    for (i = 1; i <= rows(_dash_at_R); i++) {
        if (_dash_at_R[i, 5] != "1") continue
        val = .
        rc = _dash_tdate_value(_dash_at_R[i, 2],
                               st_local("_at_xa" + _dash_at_R[i, 4]) == "2" ? u2 : u1,
                               val)
        if (rc != 1 | val >= .) {
            st_local("_at_err", _dash_at_R[i, 2])
            return(198)
        }
        _dash_at_R[i, 2] = strofreal(val, "%21.0g")
    }
    return(0)
}

// _dash_at_place(p) -- the compass direction twoway draws placement(p) in
// (n ne e se s sw w nw c), "" for a name twoway notes and draws east:
// compass2dir's reading of the word (_dash_style_word; WP-45 ST-1:
// nor, NE, rig, 3 are taken, NOR and 3.0 noted).
string scalar _dash_at_place(string scalar p)
{
    return(_dash_style_word("compass2dir", p))
}

// _dash_at_orient(o) -- the orientation twoway draws orientation(o) in:
// horizontal, vertical, rvertical or rhorizontal, "" for a name twoway
// notes and draws horizontally -- tb_orientstyle's reading of the word
// (_dash_style_word; WP-45 ST-2: hor, vertic, rhori are taken).
string scalar _dash_at_orient(string scalar o)
{
    return(_dash_style_word("tb_orientstyle", o))
}

// _dash_style_word(cls, w) -- the canonical name the style class cls
// reads the word w as, or "" for a word the class does not take (WP-45
// ST-1, D-45-02.a), as the class's _unabbrev program reads it (ado/base
// <c>/<cls>.class).  The word, blanks around it dropped, is first one of
// the class's exact words (clockdir 0-12 as written; anglestyle 45 and
// 270; connectstyle L ascending, J stairstep, stairstep_up), then a lower
// case abbreviation of one of its syntax option names in the class's
// order, at least the option's capitals long; for compass2dir a word of
// at most two characters no name took is one of its capitals N S E W NE
// NW SE SW T B R L, or a clock number 0-12.  Canonicals: compass2dir n ne
// e se s sw w nw c; tb_orientstyle horizontal vertical rhorizontal
// rvertical; clockdir 0-12; gridringstyle 0 or 1; anglestyle degrees;
// connectstyle direct ascending stairstep stepstair none.  The same
// tables as dash_render.py's _dash_style_word (_DASH_STYLE_NAMES), pinned
// row by row to test/fixtures/style_words_truth.json (cscript Q4502-3).
// Fixed tables read by value; O(len(w)).
string scalar _dash_style_word(string scalar cls, string scalar w)
{
    string matrix    T
    string rowvector caps, capv, clk
    string scalar    t
    real scalar      i, n, v

    t = strtrim(w)
    if (t == "" | strpos(t, " ") | strpos(t, char(9))) return("")
    n = strlen(t)
    if (cls == "compass2dir") {
        T = ("north", "1", "n" \ "south", "1", "s" \ "east", "1", "e" \
             "west", "1", "w" \ "nwest", "2", "nw" \ "neast", "2", "ne" \
             "swest", "2", "sw" \ "seast", "2", "se" \ "center", "1", "c" \
             "top", "1", "n" \ "bottom", "1", "s" \ "left", "1", "w" \
             "right", "1", "e")
    }
    else if (cls == "tb_orientstyle") {
        T = ("horizontal", "3", "horizontal" \ "vertical", "4", "vertical" \
             "rhorizontal", "4", "rhorizontal" \ "rvertical", "5", "rvertical")
    }
    else if (cls == "clockdir") {
        if (anyof(("0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                   "11", "12"), t)) return(t)
        T = ("center", "1", "0" \ "top", "1", "12" \ "bottom", "1", "6" \
             "left", "1", "9" \ "right", "1", "3")
    }
    else if (cls == "gridringstyle") {
        T = ("inside", "1", "0" \ "outside", "1", "1")
    }
    else if (cls == "anglestyle") {
        if (t == "45" | t == "270") return(t)
        T = ("horizontal", "1", "0" \ "vertical", "1", "90" \
             "rhorizontal", "2", "180" \ "rvertical", "2", "270")
    }
    else if (cls == "connectstyle") {
        if (t == "L") return("ascending")
        if (t == "J") return("stairstep")
        if (t == "stairstep_up") return("stepstair")
        T = ("connected", "1", "direct" \ "direct", "1", "direct" \
             "line", "1", "direct" \ "stairstep", "1", "stairstep" \
             "upstairstep", "1", "stepstair" \ "stepstair", "4", "stepstair" \
             "ascending", "1", "ascending" \ "none", "1", "none" \
             "i", "1", "none")
    }
    else return("")
    for (i = 1; i <= rows(T); i++) {
        if (n >= strtoreal(T[i, 2]) & n <= strlen(T[i, 1]) &
            substr(T[i, 1], 1, n) == t) return(T[i, 3])
    }
    if (cls != "compass2dir" | n > 2) return("")
    caps = ("N", "S", "E", "W", "NE", "NW", "SE", "SW", "T", "B", "R", "L")
    capv = ("n", "s", "e", "w", "ne", "nw", "se", "sw", "n", "s", "e", "w")
    for (i = 1; i <= cols(caps); i++) {
        if (caps[i] == t) return(capv[i])
    }
    if (!_dash_so_isnum(t, 0)) return("")
    v = strtoreal(t)
    if (v >= . | v != trunc(v) | v < 0 | v > 12) return("")
    clk = ("c", "ne", "ne", "e", "se", "se", "s", "sw", "sw", "w", "nw",
           "nw", "n")
    return(clk[v + 1])
}

// _dash_edge_span(pre) -- span or nospan given inside an edge title, which
// twoway refuses when it draws (_fr_title_parse_and_log.ado logs
// <k>_span(yes|no) as a style edit the edge title's style does not have;
// textbox_truth.json e_t1_span): "option(s) t1title_span(yes) not
// allowed", r(198), the last span or nospan of a title winning, the titles
// in twoway's parse order (graph_g.class parse_and_log_titles: r1 r2 l1
// l2 t1 t2 b1 b2).  Reads s(<pre><k>) by value -- each copy (char(30)
// between copies), its sub-options after the first top-level comma
// (_dash_first_comma_pos), split by _dash_rep_toks -- and sets the caller's
// local _es_msg to twoway's line, or "".
void _dash_edge_span(string scalar pre)
{
    string rowvector ks, t
    string scalar    v, cp, last
    real scalar      i, j, p, c

    ks = ("r1title", "r2title", "l1title", "l2title", "t1title", "t2title",
          "b1title", "b2title")
    for (i = 1; i <= cols(ks); i++) {
        v = st_global("s(" + pre + ks[i] + ")")
        if (!strpos(v, "span")) continue
        last = ""
        while (v != "") {
            p = strpos(v, char(30))
            cp = (p ? substr(v, 1, p - 1) : v)
            v = (p ? substr(v, p + 1, .) : "")
            c = _dash_first_comma_pos(cp)
            if (!c) continue
            t = _dash_rep_toks(substr(cp, c + 1, .), 1)
            for (j = 1; j <= cols(t); j++) {
                if (t[j] == "span") last = "yes"
                else if (t[j] == "nospan") last = "no"
            }
        }
        if (last != "") {
            st_local("_es_msg", "option(s) " + ks[i] + "_span(" + last +
                     ") not allowed")
            return
        }
    }
    st_local("_es_msg", "")
}

// _dash_at_globals(s) -- s with each $name and ${name} (name
// [A-Za-z_][A-Za-z0-9_]*, at most 32 characters) replaced by st_global()'s
// value, as twoway expands a text() line (WP-31 D13; textbox_truth.json
// global_plain hello, global_braces hello!, global_dollars: "$$u30f$$" is
// "$$", the inner $u30f naming F and $F empty).  Read right to left, so a
// $ just before a replaced value takes its name from that value, as
// Stata's nested $$ does; each $ of s is read once, so it ends.  A $
// followed by anything else is kept.  With ev 1 each value's =exp runs
// are evaluated by the safe evaluator first (_dash_at_exp_runs; WP-43
// LT-20, P4-6, P4-7: twoway draws a global holding `=1+1' as 2,
// global_eval), and a run it keeps as written -- an =exp it refuses, a
// macro reference -- sets the caller's local _at_expnote to 1; nothing
// from the text is run.  With ev 0 or omitted the value is text.  Stops
// once the text passes 4,000 bytes; the caller refuses that.
string scalar _dash_at_globals(string scalar s, | real scalar ev)
{
    string scalar rest, nm, v
    real scalar   i, L, nt

    if (args() < 2) ev = 0
    for (i = strlen(s); i >= 1; i--) {
        if (substr(s, i, 1) != "$") continue
        rest = substr(s, i + 1, .)
        nm = ""
        L = 0
        if (ustrregexm(rest, "^[{]([A-Za-z_][A-Za-z0-9_]*)[}]")) {
            nm = ustrregexs(1)
            L = strlen(nm) + 2
        }
        else if (ustrregexm(rest, "^([A-Za-z_][A-Za-z0-9_]*)")) {
            nm = ustrregexs(1)
            L = strlen(nm)
        }
        if (nm == "" | strlen(nm) > 32) continue
        v = st_global(nm)
        if (ev == 1) {
            nt = 0
            v = _dash_at_exp_runs(v, nt)
            if (nt == 1) st_local("_at_expnote", "1")
        }
        s = substr(s, 1, i - 1) + v + substr(rest, L + 1, .)
        if (strlen(s) > 4000) return(s)
    }
    return(s)
}

// _dash_at_exp_runs(v, nt) -- v, a global's value, with each run that
// starts `= and ends at the first ' outside a "..." inside it replaced by
// its value when the safe evaluator reads it (_dash_at_exp), as twoway
// evaluates a graph text's =exp global (WP-43 LT-20, P4-6, P4-7;
// added_text_box_truth.json x_eval_*).  Every other run -- an =exp the
// evaluator refuses, a macro reference `name' or `c(name)' -- is kept as
// written and sets nt to 1.  Nothing is run or read: the value is text.
string scalar _dash_at_exp_runs(string scalar v, real scalar nt)
{
    string scalar out, r, c
    real scalar   i, j, k, n, inq, ok

    out = ""
    n = strlen(v)
    i = 1
    while (i <= n) {
        k = strpos(substr(v, i, .), char(96))
        if (!k) {
            out = out + substr(v, i, .)
            break
        }
        out = out + substr(v, i, k - 1)
        i = i + k - 1
        inq = 0
        j = 0
        for (k = i + 1; k <= n; k++) {
            c = substr(v, k, 1)
            if (c == char(34)) inq = !inq
            else if (c == char(39) & !inq) {
                j = k
                break
            }
        }
        if (!j) {
            out = out + substr(v, i, .)
            break
        }
        if (substr(v, i + 1, 1) == "=") {
            ok = 0
            r = _dash_at_exp(substr(v, i + 2, j - i - 2), ok)
            if (ok) {
                out = out + r
                i = j + 1
                continue
            }
        }
        nt = 1
        out = out + substr(v, i, j - i + 1)
        i = j + 1
    }
    return(out)
}

// _dash_at_exp(e, ok) -- the text twoway draws for `=e' when e is made
// only of numbers, strings in double quotes, ., the operators
// + - * / ^ == != ~= > < >= <= & | ! ~, parentheses and the functions
// of wl, with ok 1; else e itself with ok 0 (WP-43 LT-20, P4-6).  A
// recursive-descent reading (_dash_at_xp, _dash_at_xf, _dash_at_xws) in
// Stata's order of evaluation as twoway draws it (x_eval_*: -2^2 is -4,
// 2^3^2 is 64, !1+1 is 1), Stata's missing rules holding.  Every value is
// computed here: nothing reaches Stata, a macro, a result, a variable or
// a file.  A number is drawn %18.0g, trimmed (x_eval_2 .3333333333333333,
// x_eval_4 1.00000000000e+20), a string as it is.  Bounds: e at most
// 4,000 bytes, nesting at most 64, 16 arguments a call, a string at most
// 4,000 bytes; past any, ok is 0.
string scalar _dash_at_exp(string scalar e, real scalar ok)
{
    string rowvector wl
    string scalar    s
    real scalar      p, t, x

    wl = ("abs", "ceil", "floor", "int", "exp", "ln", "log", "log10",
          "sqrt", "sign", "round", "mod", "min", "max", "string",
          "strofreal", "real", "strlen", "ustrlen", "substr", "usubstr",
          "upper", "strupper", "lower", "strlower", "trim", "strtrim")
    ok = 0
    if (strlen(e) > 4000 | strpos(e, char(96)) | strpos(e, char(36)))
        return(e)
    ok = 1
    p = 1
    t = 0
    x = .
    s = ""
    _dash_at_xp(e, p, 1, 0, ok, t, x, s, wl)
    if (ok) {
        _dash_at_xws(e, p)
        if (p <= strlen(e)) ok = 0
    }
    if (ok & t == 1) s = strtrim(strofreal(x, "%18.0g"))
    if (!ok | strlen(s) > 4000) {
        ok = 0
        return(e)
    }
    return(s)
}

// _dash_at_xws(e, p) -- p moved past the blanks of e at p.
void _dash_at_xws(string scalar e, real scalar p)
{
    while (p <= strlen(e) & substr(e, p, 1) == " ") p++
}

// _dash_at_xp(e, p, lvl, d, ok, t, x, s, wl) -- _dash_at_exp's reader:
// the expression of e at p at level lvl (1 |, 2 &, 3 the relations, 4 +
// -, 5 * /, 6 unary -, 7 ^ left to right, 8 ! ~ and the atoms), its value
// in t (1 a number x, 2 a string s), p moved past it; ok 0 on anything
// else.  d counts the nesting.
void _dash_at_xp(string scalar e, real scalar p, real scalar lvl,
                 real scalar d, real scalar ok, real scalar t,
                 real scalar x, string scalar s, string rowvector wl)
{
    string rowvector ops
    string colvector as
    real colvector   at, ax
    string scalar    op, c, nm, s2
    real scalar      k, q, n, t2, x2

    if (!ok) return
    if (d > 64) {
        ok = 0
        return
    }
    _dash_at_xws(e, p)
    if (lvl <= 5) {
        if (lvl == 1) ops = ("|")
        else if (lvl == 2) ops = ("&")
        else if (lvl == 3) ops = ("==", "!=", "~=", ">=", "<=", ">", "<")
        else if (lvl == 4) ops = ("+", "-")
        else ops = ("*", "/")
        _dash_at_xp(e, p, lvl + 1, d, ok, t, x, s, wl)
        while (ok) {
            _dash_at_xws(e, p)
            op = ""
            for (k = 1; k <= cols(ops); k++) {
                if (substr(e, p, strlen(ops[k])) == ops[k]) {
                    op = ops[k]
                    break
                }
            }
            if (op == "") return
            p = p + strlen(op)
            t2 = 0
            x2 = .
            s2 = ""
            _dash_at_xp(e, p, lvl + 1, d, ok, t2, x2, s2, wl)
            if (!ok) return
            if (lvl == 3) {
                if (t != t2) {
                    ok = 0
                    return
                }
                if (t == 1) {
                    if (op == "==") x = (x == x2)
                    else if (op == "!=" | op == "~=") x = (x != x2)
                    else if (op == ">=") x = (x >= x2)
                    else if (op == "<=") x = (x <= x2)
                    else if (op == ">") x = (x > x2)
                    else x = (x < x2)
                }
                else {
                    if (op == "==") x = (s == s2)
                    else if (op == "!=" | op == "~=") x = (s != s2)
                    else if (op == ">=") x = (s >= s2)
                    else if (op == "<=") x = (s <= s2)
                    else if (op == ">") x = (s > s2)
                    else x = (s < s2)
                }
                t = 1
                s = ""
                continue
            }
            if (lvl == 4 & op == "+" & t == 2 & t2 == 2) {
                if (strlen(s) + strlen(s2) > 4000) {
                    ok = 0
                    return
                }
                s = s + s2
                continue
            }
            if (t != 1 | t2 != 1) {
                ok = 0
                return
            }
            if (op == "|") x = (x != 0 | x2 != 0)
            else if (op == "&") x = (x != 0 & x2 != 0)
            else if (op == "+") x = x + x2
            else if (op == "-") x = x - x2
            else if (op == "*") x = x * x2
            else x = (x2 == 0 ? . : x / x2)
        }
        return
    }
    c = substr(e, p, 1)
    if (lvl == 6) {
        if (c != "-") {
            _dash_at_xp(e, p, 7, d, ok, t, x, s, wl)
            return
        }
        p++
        _dash_at_xp(e, p, 6, d + 1, ok, t, x, s, wl)
        if (ok & t != 1) ok = 0
        if (ok) x = -x
        return
    }
    if (lvl == 7) {
        _dash_at_xp(e, p, 8, d, ok, t, x, s, wl)
        while (ok) {
            _dash_at_xws(e, p)
            if (substr(e, p, 1) != "^") return
            p++
            _dash_at_xws(e, p)
            t2 = 0
            x2 = .
            s2 = ""
            _dash_at_xp(e, p, (substr(e, p, 1) == "-" ? 6 : 8), d + 1, ok,
                        t2, x2, s2, wl)
            if (!ok) return
            if (t != 1 | t2 != 1) {
                ok = 0
                return
            }
            x = x ^ x2
        }
        return
    }
    if ((c == "!" | c == "~") & substr(e, p + 1, 1) != "=") {
        p++
        _dash_at_xp(e, p, 8, d + 1, ok, t, x, s, wl)
        if (ok & t != 1) ok = 0
        if (ok) x = (x == 0)
        return
    }
    if (c == "(") {
        p++
        _dash_at_xp(e, p, 1, d + 1, ok, t, x, s, wl)
        if (!ok) return
        _dash_at_xws(e, p)
        if (substr(e, p, 1) != ")") {
            ok = 0
            return
        }
        p++
        return
    }
    if (c == char(34)) {
        q = strpos(substr(e, p + 1, .), char(34))
        if (!q) {
            ok = 0
            return
        }
        t = 2
        s = substr(e, p + 1, q - 1)
        p = p + q + 1
        return
    }
    if (ustrregexm(substr(e, p, 64), "^([0-9]+([.][0-9]*)?([eE][+-]?[0-9]+)?|[.][0-9]+([eE][+-]?[0-9]+)?)")) {
        nm = ustrregexs(1)
        t = 1
        x = strtoreal(nm)
        p = p + strlen(nm)
        return
    }
    if (c == ".") {
        t = 1
        x = .
        p++
        return
    }
    if (!ustrregexm(substr(e, p, 64), "^([a-z0-9_]+) *[(]")) {
        ok = 0
        return
    }
    nm = ustrregexs(1)
    if (!anyof(wl, nm)) {
        ok = 0
        return
    }
    p = p + strlen(ustrregexs(0))
    at = J(0, 1, .)
    ax = J(0, 1, .)
    as = J(0, 1, "")
    _dash_at_xws(e, p)
    if (substr(e, p, 1) == ")") p++
    else {
        n = 0
        while (ok) {
            if (n >= 16) {
                ok = 0
                return
            }
            t2 = 0
            x2 = .
            s2 = ""
            _dash_at_xp(e, p, 1, d + 1, ok, t2, x2, s2, wl)
            if (!ok) return
            n++
            at = at \ t2
            ax = ax \ x2
            as = as \ s2
            _dash_at_xws(e, p)
            c = substr(e, p, 1)
            p++
            if (c == ")") break
            if (c != ",") {
                ok = 0
                return
            }
        }
    }
    _dash_at_xf(nm, at, ax, as, ok, t, x, s)
}

// _dash_at_xf(nm, at, ax, as, ok, t, x, s) -- the whitelisted function nm
// of _dash_at_exp on the arguments' types at (1 number, 2 string), numbers
// ax and strings as, computed with the Mata function of the same meaning;
// its value in t, x, s; ok 0 for a wrong count or type.
void _dash_at_xf(string scalar nm, real colvector at, real colvector ax,
                 string colvector as, real scalar ok, real scalar t,
                 real scalar x, string scalar s)
{
    real scalar n, i, v

    n = rows(at)
    t = 1
    x = .
    s = ""
    if (anyof(("abs", "ceil", "floor", "int", "exp", "ln", "log", "log10",
               "sqrt", "sign"), nm)) {
        if (n != 1) ok = 0
        else if (at[1] != 1) ok = 0
        if (!ok) return
        v = ax[1]
        if (nm == "abs") x = abs(v)
        else if (nm == "ceil") x = ceil(v)
        else if (nm == "floor") x = floor(v)
        else if (nm == "int") x = trunc(v)
        else if (nm == "exp") x = exp(v)
        else if (nm == "ln" | nm == "log") x = ln(v)
        else if (nm == "log10") x = log10(v)
        else if (nm == "sqrt") x = sqrt(v)
        else x = sign(v)
        return
    }
    if (nm == "round" | nm == "mod" | nm == "min" | nm == "max") {
        if (n < 1 | any(at :!= 1)) ok = 0
        else if (nm == "round" & n > 2) ok = 0
        else if (nm == "mod" & n != 2) ok = 0
        if (!ok) return
        if (nm == "round") x = (n == 1 ? round(ax[1]) : round(ax[1], ax[2]))
        else if (nm == "mod") x = mod(ax[1], ax[2])
        else {
            for (i = 1; i <= n; i++) {
                if (ax[i] >= .) continue
                if (x >= .) x = ax[i]
                else if (nm == "min") x = (ax[i] < x ? ax[i] : x)
                else x = (ax[i] > x ? ax[i] : x)
            }
        }
        return
    }
    if (nm == "string" | nm == "strofreal") {
        if (n == 1) {
            if (at[1] == 1) {
                t = 2
                s = strtrim(strofreal(ax[1]))
                return
            }
        }
        else if (n == 2) {
            if (at[1] == 1 & at[2] == 2 &
                ustrregexm(as[2], "^%-?[1-9][0-9]?([.][0-9][0-9]?)?[fge]c?$")) {
                t = 2
                s = strtrim(strofreal(ax[1], as[2]))
                return
            }
        }
        ok = 0
        return
    }
    if (n < 1) {
        ok = 0
        return
    }
    if (at[1] != 2) {
        ok = 0
        return
    }
    if (nm == "substr" | nm == "usubstr") {
        if (n != 3) ok = 0
        else if (at[2] != 1 | at[3] != 1) ok = 0
        if (!ok) return
        t = 2
        s = (nm == "substr" ? substr(as[1], ax[2], ax[3])
                            : usubstr(as[1], ax[2], ax[3]))
        return
    }
    if (n != 1) {
        ok = 0
        return
    }
    if (nm == "real") x = strtoreal(as[1])
    else if (nm == "strlen") x = strlen(as[1])
    else if (nm == "ustrlen") x = ustrlen(as[1])
    else {
        t = 2
        if (nm == "upper" | nm == "strupper") s = strupper(as[1])
        else if (nm == "lower" | nm == "strlower") s = strlower(as[1])
        else if (nm == "trim" | nm == "strtrim") s = strtrim(as[1])
        else ok = 0
    }
}

// _dash_gt_qleft(s) -- s up to its first comma outside "..." and
// compound quotes: the part twoway's syntax reads before the options.
string scalar _dash_gt_qleft(string scalar s)
{
    real rowvector b
    real scalar    i, n, depth, inq

    b = ascii(s)
    n = cols(b)
    depth = 0
    inq = 0
    for (i = 1; i <= n; i++) {
        if (depth) {
            if (b[i] == 96 & i < n) {
                if (b[i + 1] == 34) {
                    depth++
                    i++
                    continue
                }
            }
            if (b[i] == 34 & i < n) {
                if (b[i + 1] == 39) {
                    depth--
                    i++
                }
            }
            continue
        }
        if (inq) {
            if (b[i] == 34) inq = 0
            continue
        }
        if (b[i] == 96 & i < n) {
            if (b[i + 1] == 34) {
                depth = 1
                i++
                continue
            }
        }
        if (b[i] == 34) inq = 1
        else if (b[i] == 44) return(substr(s, 1, i - 1))
    }
    return(s)
}

// _dash_gt_qadded(s) -- the part of option text s before its options with
// its globals expanded (_dash_at_globals), when the expansion adds a
// double quote; "" otherwise.  twoway reads a graph text option's whole
// text again before its quotes (WP-31 D13b, global_text_truth.json), so
// such a global splits the string; the caller refuses where twoway does.
// ev as _dash_at_globals takes it (WP-43 LT-20).
string scalar _dash_gt_qadded(string scalar s, | real scalar ev)
{
    string scalar l, e

    if (args() < 2) ev = 0
    if (!strpos(s, "$")) return("")
    l = _dash_gt_qleft(s)
    // A copy: _dash_at_globals rewrites its argument in place.
    e = _dash_at_globals(l + "", ev)
    if (sum(ascii(e) :== 34) > sum(ascii(l) :== 34)) return(e)
    return("")
}

// _dash_gt_qtexts(raw) -- 1, with the global dash__q set to the expanded
// points and lines, for the first char(30)-separated copy of a text() or
// ttext() whose globals add a double quote (_dash_gt_qadded); 0 when
// none does.  dash.ado's _dash_at_quote_refuse then reads it as twoway's
// _parse_log_1textbox does.
real scalar _dash_gt_qtexts(string scalar raw)
{
    real rowvector ix
    real scalar    k, a, z
    string scalar  e

    st_global("dash__q", "")
    if (!strpos(raw, "$")) return(0)
    ix = (0, selectindex(ascii(raw) :== 30), strlen(raw) + 1)
    for (k = 1; k < cols(ix); k++) {
        a = ix[k] + 1
        z = ix[k + 1]
        e = _dash_gt_qadded(substr(raw, a, z - a), 1)
        if (e != "") {
            st_global("dash__q", e)
            return(1)
        }
    }
    return(0)
}

// _dash_gt_ccl(s) -- s with each {ccl name} replaced by c(name) as
// twoway's graph text draws it (WP-31 E9, smcl_text_truth.json smcl.ccl):
// a string as it is, a number in Mata's %18.0g (c(pi) 3.141592653589793,
// c(maxdouble) 8.9884656743e+307), an unknown name as nothing, and
// c(version) as 9, the version twoway draws under.  Blanks
// around the head and between ccl and the name are read (within 80
// bytes of the brace); the name is [A-Za-z_][A-Za-z0-9_]*, at most 32
// characters; {ccl name:...} and any other form are kept.  Each { is
// looked at once and the pieces joined once, so it is linear; a value is
// never read again.  dash.ado applies it to the
// graph's text options and text()/ttext() lines at registration, where
// the renderer cannot read c().
string scalar _dash_gt_ccl(string scalar s)
{
    string rowvector pc
    string scalar    nm, whole, val
    transmorphic     v
    real rowvector   ix
    real scalar      i, k, m, last

    if (!ustrregexm(s, "[{][ \t]*ccl[ \t]")) return(s)
    ix = selectindex(ascii(s) :== 123)
    pc = J(1, 2 * cols(ix) + 1, "")
    m = 0
    last = 1
    for (k = 1; k <= cols(ix); k++) {
        i = ix[k]
        if (i < last) continue
        if (!ustrregexm(substr(s, i, 80), "^[{][ \t]*ccl[ \t]+([A-Za-z_][A-Za-z0-9_]*)[ \t]*[}]")) continue
        nm = ustrregexs(1)
        whole = ustrregexs(0)
        if (strlen(nm) > 32) continue
        v = c(nm)
        // twoway draws its graph text under version 9: {ccl version} is 9
        // whatever version the caller runs (smcl_more_truth.json
        // ccl.version, ccl.version16, ccl.version19prog).
        if (nm == "version") val = "9"
        else if (eltype(v) == "string") val = v
        else val = strtrim(strofreal(v, "%18.0g"))
        pc[++m] = substr(s, last, i - last)
        pc[++m] = val
        last = i + strlen(whole)
    }
    pc[++m] = substr(s, last, .)
    return(invtokens(pc[|1 \ m|], ""))
}

// _dash_at_json(kind, y, x, ya, xa, lines, opts) -- one added_text record:
// {"at_kind":..,"at_y":..,"at_x":..,"at_yaxis":..,"at_xaxis":..,
// "at_lines":[..],"at_opts":".."}.  Numbers in %21.0g; lines already a
// JSON array and opts already _dash_json_escape()d (_dash_at_opts), written as
// they come.  Every key starts at_, so no substring reader of the graph's
// JSON (_dash_json_first_num) finds one.
string scalar _dash_at_json(string scalar kind, real scalar y,
                            real scalar x, real scalar ya, real scalar xa,
                            string scalar lines, string scalar opts)
{
    string scalar q

    q = char(34)
    return("{" + q + "at_kind" + q + ":" + q + kind + q + "," +
           q + "at_y" + q + ":" + strtrim(strofreal(y, "%21.0g")) + "," +
           q + "at_x" + q + ":" + strtrim(strofreal(x, "%21.0g")) + "," +
           q + "at_yaxis" + q + ":" + strofreal(ya) + "," +
           q + "at_xaxis" + q + ":" + strofreal(xa) + "," +
           q + "at_lines" + q + ":" + lines + "," +
           q + "at_opts" + q + ":" + q + opts + q + "}")
}

// _dash_at_records(kind) -- the last _dash_at_parse's records as one
// comma-joined list of _dash_at_json() objects, into the caller's local
// _at_json; each copy's axes and drawn sub-options are the caller's
// locals _at_ya<k>, _at_xa<k> and _at_cn<k> (_dash_at_opts), and a
// converted date's value its _dash_at_R column 2.
void _dash_at_records(string scalar kind)
{
    external string matrix _dash_at_R
    string colvector r
    string scalar    k
    real scalar      i, n

    n = rows(_dash_at_R)
    r = J(n, 1, "")
    for (i = 1; i <= n; i++) {
        k = _dash_at_R[i, 4]
        r[i] = _dash_at_json(kind, strtoreal(_dash_at_R[i, 1]),
                             strtoreal(_dash_at_R[i, 2]),
                             strtoreal(st_local("_at_ya" + k)),
                             strtoreal(st_local("_at_xa" + k)),
                             _dash_at_R[i, 3], st_local("_at_cn" + k))
    }
    st_local("_at_json", n ? invtokens(r', ",") : "")
}

// _dash_at_canon() -- the drawn sub-options of one copy, read from the
// caller's (_dash_at_opts's) syntax locals by value, in full names:
// size() color() tstyle() justification() alignment() orientation() box or
// nobox fcolor() lcolor() lwidth() lpattern() lstyle() lalign() linegap()
// width() height() margin() placement(), bfcolor() blcolor() blwidth()
// blpattern() blstyle() blalign() standing in for the plain ones when those are absent and bcolor() for
// both colours when neither is given; _dash_json_escape()d.  orientation()
// and placement() are dash.ado's canonical names (_dash_at_orient,
// _dash_at_place); a name twoway notes is left out.
string scalar _dash_at_canon()
{
    string scalar out, v, fc, lc, lw, o, p

    out = ""
    v = st_local("size")
    if (v != "") out = out + " size(" + v + ")"
    v = st_local("color")
    if (v != "") out = out + " color(" + v + ")"
    v = st_local("tstyle")
    if (v != "") out = out + " tstyle(" + v + ")"
    v = st_local("justification")
    if (v != "") out = out + " justification(" + v + ")"
    // alignment() as typed: twoway draws only the four full words as
    // themselves (added_text_box_truth.json al_<x>); the renderer names
    // any other value as twoway does and draws it as bottom.
    v = st_local("alignment")
    if (v != "") out = out + " alignment(" + v + ")"
    o = _dash_at_orient(st_local("orientation"))
    if (o != "") out = out + " orientation(" + o + ")"
    if (st_local("box") != "" & st_local("nobox") == "") out = out + " box"
    else if (st_local("nobox") != "") out = out + " nobox"
    fc = st_local("fcolor")
    if (fc == "") fc = st_local("bfcolor")
    lc = st_local("lcolor")
    if (lc == "") lc = st_local("blcolor")
    if (fc == "" & lc == "" & st_local("bcolor") != "") {
        fc = st_local("bcolor")
        lc = fc
    }
    if (fc != "") out = out + " fcolor(" + fc + ")"
    if (lc != "") out = out + " lcolor(" + lc + ")"
    lw = st_local("lwidth")
    if (lw == "") lw = st_local("blwidth")
    if (lw != "") out = out + " lwidth(" + lw + ")"
    // WP-43 LT-20: the frame's pattern, style and alignment (the bl forms
    // standing in), the line gap and the fixed box.
    v = st_local("lpattern")
    if (v == "") v = st_local("blpattern")
    if (v != "") out = out + " lpattern(" + v + ")"
    v = st_local("lstyle")
    if (v == "") v = st_local("blstyle")
    if (v != "") out = out + " lstyle(" + v + ")"
    v = st_local("lalign")
    if (v == "") v = st_local("blalign")
    if (v != "") out = out + " lalign(" + v + ")"
    v = st_local("linegap")
    if (v != "") out = out + " linegap(" + v + ")"
    v = st_local("width")
    if (v != "") out = out + " width(" + v + ")"
    v = st_local("height")
    if (v != "") out = out + " height(" + v + ")"
    v = st_local("margin")
    if (v != "") out = out + " margin(" + v + ")"
    p = st_local("placement")
    if (p != "") {
        p = _dash_at_place(p)
        out = out + " placement(" + (p != "" ? p : "e") + ")"
    }
    return(_dash_json_escape(strtrim(out)))
}

// _dash_rep_reduce(opts, ptype) -- the option list with one copy of each
// option, as twoway reads it.  Each word's option is the key the parser
// gave its typed name (the caller's locals _rp_n, _rp_nm<i>, _rp_key<i>,
// set by dash.ado's _dash_opts_repeats); a word whose name has no key is
// left as typed, for the ignoring note.  An option given more than once
// stands where its last copy stood: that copy as typed when the option is
// rightmost, else name(merged value) under the last copy's spelling.  A
// unique option given twice sets the caller's local _rp_refuse to the
// second copy's name as typed, "()" after it when it took a value --
// twoway's words, "option bwid() not allowed" -- and the list is returned
// unchanged.  Linear in the number of words times the distinct names.
string scalar _dash_rep_reduce(string scalar opts, string scalar ptype)
{
    string rowvector toks, keys, names, nkeys, val
    string scalar    nm, out
    real rowvector   cnt, lastpos
    real scalar      i, j, n, k, nk

    st_local("_rp_refuse", "")
    st_local("_rp_refuse_g", "0")
    n     = strtoreal(st_local("_rp_n"))
    names = J(1, n, "")
    nkeys = J(1, n, "")
    for (i = 1; i <= n; i++) {
        names[i] = st_local("_rp_nm" + strofreal(i))
        nkeys[i] = st_local("_rp_key" + strofreal(i))
    }
    toks = _dash_rep_toks(opts, 0)
    keys = J(1, cols(toks), "")
    for (i = 1; i <= cols(toks); i++) {
        nm = _dash_rep_optname(toks[i])
        if (nm == "") continue
        nm = nm + (strpos(toks[i], "(") ? "(" : "")
        for (j = 1; j <= n; j++) {
            if (names[j] == nm) {
                keys[i] = nkeys[j]
                // bins() folds into bin(): keyed apart, as twoway refuses
                // a second bins() and takes a second bin().
                if (nm == "bins(") keys[i] = keys[i] + "|bins"
                break
            }
        }
    }
    // Per key: how many copies, where the last stands, the merged value.
    nkeys   = J(1, 0, "")
    cnt     = J(1, 0, .)
    lastpos = J(1, 0, .)
    val     = J(1, 0, "")
    for (i = 1; i <= cols(toks); i++) {
        if (keys[i] == "") continue
        k = 0
        for (j = 1; j <= cols(nkeys); j++) {
            if (nkeys[j] == keys[i]) {
                k = j
                break
            }
        }
        if (!k) {
            nkeys   = nkeys, keys[i]
            cnt     = cnt, 1
            lastpos = lastpos, i
            val     = val, _dash_rep_value(toks[i])
            continue
        }
        if (_dash_rep_unique(subinstr(keys[i], "|bins", ""),
                             _dash_rep_optname(toks[i]), ptype)) {
            st_local("_rp_refuse", _dash_rep_optname(toks[i]) +
                     (strpos(toks[i], "(") ? "()" : ""))
            // WP-32: the graph's own once-only options, which twoway
            // refuses after the plots' options and their kernel.
            st_local("_rp_refuse_g", strofreal(anyof(("name", "saving",
                     "scheme", "aspectratio", "xsize", "ysize", "scale",
                     "fxsize", "fysize", "nodraw", "play"),
                     _dash_rep_bare(subinstr(keys[i], "|bins", "")))))
            return(opts)
        }
        cnt[k]     = cnt[k] + 1
        // sort(varlist): the rightmost copy that is not empty stands, as
        // twoway reads it (WP-29 P0.1 M4); an empty copy is left out with
        // the others.
        if (!(keys[i] == "sort1" & strtrim(_dash_rep_value(toks[i])) == "")) {
            lastpos[k] = i
        }
        val[k]     = _dash_rep_merge(keys[i], val[k], _dash_rep_value(toks[i]))
    }
    nk  = 0
    for (j = 1; j <= cols(cnt); j++) nk = nk + (cnt[j] > 1)
    if (!nk) return(opts)
    out = ""
    for (i = 1; i <= cols(toks); i++) {
        if (keys[i] != "") {
            for (j = 1; j <= cols(nkeys); j++) {
                if (nkeys[j] == keys[i]) break
            }
            if (cnt[j] > 1) {
                if (lastpos[j] != i) continue
                if (_dash_rep_cat(keys[i]) != "R") {
                    out = out + " " + _dash_rep_optname(toks[i]) + "(" + val[j] + ")"
                    continue
                }
            }
        }
        out = out + " " + toks[i]
    }
    return(strtrim(out))
}

// _dash_scale_exclusive(words, kept) -- twoway's refusal of one scale
// copy's transform words, or "" (WP-44 AX-10; axis_scale_truth.json
// ax10_*, ax9_no_forms).  _gs_parse_and_log_axoptions.ado reads the copy
// with -syntax- (NOLOG LOG NOATANH ATANH NOLOGIT LOGIT NOLOG1m LOG1m),
// then runs opts_exclusive over the eight in that order.  As -syntax-
// binds them: a no form given again sets the same local (nolog nolog is
// drawn); a second log binds LOG1m, whose shortest form is log (log log is
// "log or log1m"); any other word given again is left for
// _dash_so_resolve ("option logit not allowed").  kept is words less the
// no forms given again, a second log written log1m.  Two or more names
// give opts_exclusive's line: "only one of options a or b is allowed",
// "only one of options a, b, or c is allowed".
string scalar _dash_scale_exclusive(string rowvector words,
                                    string rowvector kept)
{
    string rowvector order, seen, got
    string scalar    nm, msg
    real scalar      i, n

    order = ("nolog", "log", "noatanh", "atanh", "nologit", "logit",
             "nolog1m", "log1m")
    kept = J(1, 0, "")
    seen = J(1, 0, "")
    for (i = 1; i <= cols(words); i++) {
        nm = (strpos(words[i], "(") ? "" :
              _dash_so_canon(strtrim(words[i]), "axscale"))
        if (!anyof(order, nm)) {
            kept = kept, words[i]
            continue
        }
        if (anyof(seen, nm)) {
            if (substr(nm, 1, 2) == "no") continue
            if (nm == "log") {
                if (!anyof(seen, "log1m")) {
                    seen = seen, "log1m"
                    kept = kept, "log1m"
                }
                continue
            }
            kept = kept, words[i]
            continue
        }
        seen = seen, nm
        kept = kept, words[i]
    }
    got = J(1, 0, "")
    for (i = 1; i <= cols(order); i++) {
        if (anyof(seen, order[i])) got = got, order[i]
    }
    n = cols(got)
    if (n < 2) return("")
    if (n == 2) return("only one of options " + got[1] + " or " + got[2] +
                       " is allowed")
    msg = "only one of options "
    for (i = 1; i < n; i++) msg = msg + got[i] + ", "
    return(msg + "or " + got[n] + " is allowed")
}

// _dash_scale_untransformable(v) -- 1 when the last of twoway's eight
// transform words (nolog log noatanh atanh nologit logit nolog1m log1m,
// any abbreviation: log1 is log1m) in the scale value v is atanh, logit or
// log1m.  v is the option's copies merged in the order typed
// (_dash_rep_merge keeps a word given again last and drops a word its no
// form cancels).  twoway's parser takes the three words, but its graph
// fails on an axis that keeps one, "unrecognized command", r(199) -- on
// xscale(), yscale(), tscale() and zscale(), alt beside it or a later copy
// without a transform word -- and draws the plain graph when a later copy
// gives log, nolog or a no form (WP-44 AX-9, ruling D75: Stata's scales
// are linear or log; test/fixtures/axis_scale_truth.json ax9_*).  A word
// holding a parenthesis (range(), lcolor()) is no transform word.
real scalar _dash_scale_untransformable(string scalar v)
{
    string rowvector toks, words
    string scalar    nm, last
    real scalar      i

    words = ("nolog", "log", "noatanh", "atanh", "nologit", "logit",
             "nolog1m", "log1m")
    toks = _dash_rep_toks(v, 0)
    last = ""
    for (i = 1; i <= cols(toks); i++) {
        if (strpos(toks[i], "(")) continue
        nm = _dash_so_canon(strtrim(toks[i]), "axscale")
        if (anyof(words, nm)) last = nm
    }
    return(anyof(("atanh", "logit", "log1m"), last))
}

// _dash_spec_types_in(s, allowed) -- 1 when the graph spec s names a plot
// type and every type it names is a word of allowed.
//
// dash.ado asks it of a graph that names no variable: a graph whose plots
// are all scatteri, pci, pcarrowi or function draws from its own values
// and needs no data, as twoway draws them with none in memory; any other
// such graph was not registered by this dash (P1A-69) and is refused.  A
// type is read as the spec writes it, "type":"<name>", and matched whole,
// its closing quote included, so pcarrowi is not pci.  A key written
// inside a string -- a title holding "type":"scatter" -- is text: its
// quotes are escaped there, so it is never counted.  Linear in the length
// of s: each count is one subinstr() over it, and a word given twice in
// allowed is counted once.
real scalar _dash_spec_types_in(string scalar s, string scalar allowed)
{
    string rowvector ok
    string scalar    key, k
    real scalar      n, m, i

    key = char(34) + "type" + char(34) + ":" + char(34)
    n   = (strlen(s) - strlen(subinstr(s, key, "", .))) / strlen(key)
    if (n == 0) return(0)
    ok = tokens(allowed)
    if (cols(ok) == 0) return(0)
    ok = uniqrows(ok')'
    m  = 0
    for (i = 1; i <= cols(ok); i++) {
        k = key + ok[i] + char(34)
        m = m + (strlen(s) - strlen(subinstr(s, k, "", .))) / strlen(k)
    }
    return(m == n)
}

// _dash_spec_has_plots(json) -- 1 when the spec's "plots" array holds a
// record, 0 when it is empty ("plots":[]): bare dash, as bare twoway,
// registers an empty graph that needs no variable (WP-31 A1).  Byte scan, no regex.
real scalar _dash_spec_has_plots(string scalar json)
{
    real scalar p, q, n

    p = strpos(json, char(34) + "plots" + char(34))
    if (!p) return(0)
    q = strpos(substr(json, p, .), "[")
    if (!q) return(0)
    q = p + q
    n = strlen(json)
    // Mata's & does not short-circuit, so the bound is tested on its own
    // (ascii("") is 1x0 and anyof would error past the end).
    while (q <= n) {
        if (!anyof((32, 9, 10, 13), ascii(substr(json, q, 1)))) break
        q++
    }
    if (q > n) return(0)
    return(substr(json, q, 1) == "{")
}

// The first "key":"<digits>" value in s, or missing when key is absent or
// its value is not all ASCII digits (bin() is twoway's own non-negative
// integer suboption; anything else here is a generator bug, never typed
// by a user into JSON directly).
real scalar _dash_json_first_num(string scalar s, string scalar key) {
    string scalar needle, val
    real scalar   pos, vstart, vend

    needle = char(34) + key + char(34) + ":" + char(34)
    pos = strpos(s, needle)
    if (!pos) return(.)
    vstart = pos + strlen(needle)
    vend = strpos(substr(s, vstart, .), char(34))
    if (!vend) return(.)
    val = substr(s, vstart, vend - 1)
    if (!regexm(val, "^[0-9]+$")) return(.)
    return(strtoreal(val))
}

// _dash_bcal_json(cal, lo, hi) -- business calendar cal's days lo..hi as
// the spec holds them (WP-31 G7): {"min":lo,"td":[dofb(lo, cal), ...]},
// each day _dash_json_number17's (null where dofb() is missing).
string scalar _dash_bcal_json(string scalar cal, real scalar lo,
                              real scalar hi)
{
    real rowvector k
    string colvector t

    if (lo >= . | hi >= . | hi < lo) return("")
    k = lo..hi
    t = _dash_json_number17(dofb(k, cal)')
    return("{" + char(34) + "min" + char(34) + ":" + strofreal(lo, "%21.0g") +
           "," + char(34) + "td" + char(34) + ":[" + invtokens(t', ",") + "]}")
}

// _dash_fn_panel_count(byraw, touse) -- the panels by(byraw) draws over
// the rows where the variable touse is 1 (the
// distinct value combinations, missing ones left out unless `missing',
// plus one for `total'), for the function layers dash.ado evaluates once
// per panel (WP-31 C12).  -1 when a by() variable is not in the data.
real scalar _dash_fn_panel_count(string scalar byraw, string scalar touse)
{
    string scalar   vl, op
    string rowvector vars
    string matrix   key
    real colvector  keep
    real scalar     p, i, idx, n, miss, tot

    p = strpos(byraw, ",")
    vl = p ? substr(byraw, 1, p - 1) : byraw
    op = p ? " " + strlower(substr(byraw, p + 1, .)) + " " : ""
    miss = ustrregexm(op, "[ ,](mis|miss|missi|missin|missing)[ ,(]")
    tot  = ustrregexm(op, "[ ,](tot|tota|total)[ ,(]")
    vars = tokens(vl)
    if (cols(vars) == 0) return(-1)
    n = st_nobs()
    key = J(n, cols(vars), "")
    keep = st_data(., touse) :== 1
    for (i = 1; i <= cols(vars); i++) {
        idx = _st_varindex(vars[i], 1)
        if (idx == .) return(-1)
        if (st_isstrvar(idx)) {
            key[., i] = st_sdata(., idx)
            if (!miss) keep = keep :* (key[., i] :!= "")
        }
        else {
            key[., i] = strofreal(st_data(., idx), "%21x")
            if (!miss) keep = keep :* (st_data(., idx) :< .)
        }
    }
    key = select(key, keep)
    n = rows(key) ? rows(uniqrows(key)) : 0
    return(n + tot)
}

// _dash_range_panel(rp, p) -- the p-th (from 1) "|"-separated pair of rp,
// trimmed, or "" when p is out of range (WP-41 BY-27).  rp is
// _dash_fold_range's s(range_panels): each by() panel's "lo hi" of a
// range(varname), ". ." for a panel holding no value of it.
string scalar _dash_range_panel(string scalar rp, real scalar p)
{
    string rowvector parts

    if (rp == "" | p >= . | p < 1 | p != trunc(p)) return("")
    parts = tokens(rp, "|")
    parts = select(parts, parts :!= "|")
    if (p > cols(parts)) return("")
    return(strtrim(parts[p]))
}

// _dash_reflines_positions(gjson) -- the reference-line positions of one
// graph's JSON: the blank-separated tokens of every copy of xline(),
// yline(), xline2() and yline2() (WP-30 P1.21a).  dash.ado has already
// written each copy's positions as Stata's numlist expanded them
// (_dash_line_expand); a copy is a top-level-comma segment whose first
// non-blank byte is a digit, +, -, . or (.  The caller's local
// _drl_val is used as scratch.  Linear in the text.
real scalar _dash_reflines_positions(string scalar gjson)
{
    string rowvector keys
    string scalar    rest, seg, c
    real scalar      i, p, n

    keys = ("xline", "yline", "xline2", "yline2")
    n = 0
    for (i = 1; i <= cols(keys); i++) {
        _dash_json_get_str(gjson, keys[i], "_drl_val")
        rest = st_local("_drl_val")
        while (rest != "") {
            p = _dash_first_comma_pos(rest)
            if (p) {
                seg  = substr(rest, 1, p - 1)
                rest = substr(rest, p + 1, .)
            }
            else {
                seg  = rest
                rest = ""
            }
            seg = strtrim(seg)
            c   = substr(seg, 1, 1)
            if (c != "" & (strpos("0123456789+-.(", c))) {
                n = n + cols(tokens(seg))
            }
        }
    }
    st_local("_drl_val", "")
    return(n)
}

// "" when every exclude() name of group is a bare word -- the registry
// check itself is _dash_filter_refusal's, which calls this so the two
// readers of a group's exclude() names cannot drift apart.  Factored out
// of _dash_filter_refusal (WP-28 section 08; the function's text as S07
// leaves it, S07 landing first in the batch merge order).
string rowvector _dash_filter_excludes(string scalar group) {
    string rowvector items, names, out
    string scalar    tok, inner
    real scalar      t, p, k

    items = _dash_filter_items(group)
    out = J(1, 0, "")
    for (t = 2; t <= cols(items); t++) {
        tok = items[t]
        p   = strpos(tok, "(")
        if (!p) continue
        inner = strlower(_dash_blank_trim(substr(tok, 1, p - 1)))
        if (inner != "exclude") continue
        inner = substr(tok, p + 1, .)
        if (substr(inner, strlen(inner), 1) == ")") {
            inner = substr(inner, 1, strlen(inner) - 1)
        }
        names = _dash_blank_words(inner)
        for (k = 1; k <= cols(names); k++) {
            out = out, names[k]
        }
    }
    return(out)
}


// _dash_angle_out(s) -- 1 when s, stripped, is twoway's real literal and
// lies outside -360..360, else 0 (WP-30 P1.18a).  twoway refuses such an
// angle() on every axis label and tick family when it draws, r(198),
// "textangle must be between -360.000 and 360.000"; a name, or a number
// within the bounds, is no refusal.  No regex.
real scalar _dash_angle_out(string scalar s)
{
    real scalar a

    if (!_dash_so_isnum(strtrim(s), 0)) return(0)
    a = strtoreal(strtrim(s))
    if (a >= .) return(0)
    return(a < -360 | a > 360)
}

// _dash_axbound_list() -- the merged axis options twoway bounds when it
// draws (WP-30 P1.18a), listed in the calling program's locals: _axb_n
// and, per finding j, _axb_k<j> ("l" a scale's lwidth(), "a" an angle()),
// _axb_o<j> the option's name and _axb_v<j> the argument as typed.  The
// order is twoway's, measured in StataNow 19.5: axis by axis y1, x1, y2,
// x2, and on one axis the scale first, then the label, tick, mlabel and
// mtick families (axis 2: label2, tick2, then mlabel2 and mtick2, WP-31
// D1c; measured, test/fixtures/axis_look_truth.json m2_angle_*).  It reads the caller's merged
// locals g_<option>; each value is parsed under twoway's axis-1 spelling
// (_dash_axfam knows no label2 row) and resolved with _dash_so_resolve.  A
// scale's last lwidth() is always listed (the caller bounds it 0..10000
// with _dash_validate_value); a label or tick family's last angle() only
// when _dash_angle_out is 1.  Linear in the words; no regex.
void _dash_axbound_list()
{
    string matrix    fam, plan
    string rowvector words, names
    string scalar    d, v, body, dcw, badw, msg, val, opt, last, sd, fw
    real scalar      i, j, k, r, nax, n, axpos, at, sc

    fam  = _dash_axfam()
    plan = ("y", "scale", "scale" \ "y", "label", "label" \
            "y", "tick", "tick" \ "y", "mlabel", "mlabel" \
            "y", "mtick", "mtick" \
            "x", "scale", "scale" \ "x", "label", "label" \
            "x", "tick", "tick" \ "x", "mlabel", "mlabel" \
            "x", "mtick", "mtick" \
            "y", "scale2", "scale" \ "y", "label2", "label" \
            "y", "tick2", "tick" \
            "y", "mlabel2", "mlabel" \ "y", "mtick2", "mtick" \
            "x", "scale2", "scale" \ "x", "label2", "label" \
            "x", "tick2", "tick" \
            "x", "mlabel2", "mlabel" \ "x", "mtick2", "mtick")
    k = 0
    for (i = 1; i <= rows(plan); i++) {
        sd  = plan[i, 1]
        opt = sd + plan[i, 2]
        fw  = plan[i, 3]
        val = st_local("g_" + opt)
        if (strtrim(val) == "") continue
        if (!_dash_ax_parse(sd + fw + "(" + val + ")", fam, d, r, v, body,
                            words, dcw, nax, n, badw, axpos)) continue
        if (!cols(words)) continue
        sc = (fw == "scale")
        (void) _dash_so_resolve(words, J(1, cols(words), 1),
                                (sc ? "axscale" : "axlabel"), names, msg, at)
        last = ""
        for (j = 1; j <= cols(words); j++) {
            if (names[j] == (sc ? "lwidth" : "angle") &
                strpos(words[j], "(")) last = _dash_rep_value(words[j])
        }
        if (last == "" & !sc) continue
        if (!sc) {
            if (!_dash_angle_out(last)) continue
        }
        else {
            // A scale with no lwidth() lists nothing.
            if (last == "") {
                for (j = 1; j <= cols(words); j++) {
                    if (names[j] == "lwidth") break
                }
                if (j > cols(words)) continue
            }
        }
        k++
        st_local("_axb_k" + strofreal(k), (sc ? "l" : "a"))
        st_local("_axb_o" + strofreal(k), opt)
        st_local("_axb_v" + strofreal(k), last)
    }
    st_local("_axb_n", strofreal(k))
}

// ============================================================
// Zero observations (WP-37 DG-1)
// ============================================================

// _dash_zero_obs_rule(t, c) -- twoway's answer when plot type t has no
// observation in case c ("nodata", "none", "allmissing", "byempty"):
// (rc, note line, error line); rc "0" draws.  Measured
// (test/fixtures/zero_obs_truth.json, scripts/extract_zero_obs_truth.do);
// "nodata" is the registration-time refusals' answer on no data,
// compared with twoway live by test_wp37_truth.cscript Q3701-3.
// mband and mspline refuse only without bands(): the caller asks.
string rowvector _dash_zero_obs_rule(string scalar t, string scalar c)
{
    if (c == "byempty") return(("198", "", "nothing to graph"))
    if (anyof(("lpoly", "lpolyci"), t))
        return(("2000", "", "no observations"))
    if (c == "allmissing") return(("0", "", ""))
    if (anyof(("fpfit", "fpfitci"), t))
        return(("198", "(note:  fracpoly could not fit model)",
                "observation numbers out of range"))
    if (anyof(("mband", "mspline"), t))
        return(("198", "", "bands must be between 1 and 200"))
    if (t == "histogram" & c == "nodata")
        return(("198", "", "observation numbers out of range"))
    return(("0", "", ""))
}

// _dash_zero_obs_cvrule(c, discrete) -- twoway's answer when a colorvar()
// layer has no observation in case c ("nodata" or "none"): (rc, line 1,
// line 2), rc "0" drawing.  Measured (test/fixtures/
// colorvar_refusal_truth.json E_*, scripts/extract_colorvar_refusal_
// truth.do): twoway stops with r(3001) when it draws the layer, its key's
// levels made from no value, and prints these two lines; a colordiscrete
// layer (colorvar(i.x) too) and an all-missing one are drawn.  A by()
// graph is judged by byempty alone (_dash_zero_obs_rule).
string rowvector _dash_zero_obs_cvrule(string scalar c, real scalar discrete)
{
    if (discrete | !anyof(("nodata", "none"), c)) return(("0", "", ""))
    return(("3001",
            "          _calc_levels():  3001  incorrect number of arguments",
            "                 <istmt>:     -  function returned error"))
}

// _dash_zo_records(json, pend) -- the records of json's first "plots"
// array, each its own JSON text, in order: split at depth 1 outside
// strings.  pend is set to the byte offset of the ] that closes the
// array (0 when json has none): the graph's own keys -- its qual_col,
// qual_col_total, if_expr, in_expr and graph_options -- come after it
// (_dash_plot writes {"plots":[...],"graph_options":...,"if_expr":
// ...,"in_expr":...}, and _dash_qual_rewrite puts qual_col after
// in_expr), while every plot record holds keys of the same names.
string colvector _dash_zo_records(string scalar json, real scalar pend)
{
    real rowvector   b
    real scalar      n, i, at, d, inq, from
    string colvector out

    out  = J(0, 1, "")
    pend = 0
    at   = strpos(json, char(34) + "plots" + char(34) + ":[")
    if (at == 0) return(out)
    b    = ascii(json)
    n    = cols(b)
    d    = 0
    inq  = 0
    from = 0
    for (i = at + 9; i <= n; i++) {
        if (inq) {
            if (b[i] == 92) i++
            else if (b[i] == 34) inq = 0
            continue
        }
        if (b[i] == 34) {
            inq = 1
            continue
        }
        if (b[i] == 123 | b[i] == 91) {
            d++
            if (d == 1 & b[i] == 123) from = i
        }
        else if (b[i] == 125 | b[i] == 93) {
            d--
            if (d < 0) {
                pend = i
                return(out)
            }
            if (d == 0 & b[i] == 125 & from > 0) {
                out  = out \ substr(json, from, i - from + 1)
                from = 0
            }
        }
    }
    return(out)
}

// ============================================================
// Selected rows (WP-40 plat:PT-7)
// ============================================================
// When nothing on the page needs every row (the one-line form; a saved
// dash build with no filter(), link(), brush(), csv or KPI card) dash
// exports only the rows some graph draws: the page plan's own rule
// (dash_render.py _dash_embed_plan), plus a by() graph's panel rows,
// marked in Stata after every working column is made.

// _dash_sel_col(c) -- the rows qualifier column c holds 1 on; every row
// when c is "".  A name that is not a variable is an error, never skipped.
real colvector _dash_sel_col(string scalar c)
{
    if (c == "") return(J(st_nobs(), 1, 1))
    if (_st_varindex(c) >= .) {
        _error(3500, "qualifier column " + c + " is not a variable")
    }
    return(st_data(., c) :== 1)
}

// _dash_sel_mark(var, gjson) -- ORs into the byte variable var the rows
// graph gjson draws: per plot record whose type is not scatteri, pci,
// pcarrowi or function, the rows of the graph's and the plot's qualifier
// columns (G & P), and, when the graph or a kept plot carries a by(,
// total) twin, the Total rows (Gt & Pt, each its own column when it has
// no twin).  Under by() a graph also marks its G (or G | Gt) rows, whose
// by() groups are its panels, so a graph of literal plots alone marks
// those and, without by(), none.  A
// lowess layer with adjust marks every row: its mean reads every
// observation.  The graph's own keys are read after the plots array
// (_dash_zo_records sets pe to the ] that closes it).
void _dash_sel_mark(string scalar var, string scalar gjson)
{
    string colvector recs
    string scalar    tail, g, gt, by, t, p, pt, adj
    real colvector   s
    real scalar      pe, i, kept, tot, adj_all

    pe = 0
    adj_all = 0
    recs = _dash_zo_records(gjson, pe)
    tail = substr(gjson, pe + 1, .)
    _dash_json_get_str(tail, "qual_col", "_sm_g")
    _dash_json_get_str(tail, "qual_col_total", "_sm_gt")
    _dash_json_get_str(tail, "by", "_sm_by")
    g  = st_local("_sm_g")
    gt = st_local("_sm_gt")
    by = st_local("_sm_by")
    tot = (gt != "")
    for (i = 1; i <= rows(recs); i++) {
        _dash_json_get_str(recs[i], "type", "_sm_t")
        if (anyof(("scatteri", "pci", "pcarrowi", "function"),
                  strlower(st_local("_sm_t")))) continue
        _dash_json_get_str(recs[i], "qual_col_total", "_sm_pt")
        if (st_local("_sm_pt") != "") tot = 1
    }
    s = J(st_nobs(), 1, 0)
    kept = 0
    for (i = 1; i <= rows(recs); i++) {
        _dash_json_get_str(recs[i], "type", "_sm_t")
        t = strlower(st_local("_sm_t"))
        if (anyof(("scatteri", "pci", "pcarrowi", "function"), t)) continue
        kept++
        _dash_json_get_str(recs[i], "qual_col", "_sm_p")
        _dash_json_get_str(recs[i], "qual_col_total", "_sm_pt")
        p  = st_local("_sm_p")
        pt = st_local("_sm_pt")
        s = s :| (_dash_sel_col(g) :& _dash_sel_col(p))
        if (tot) {
            s = s :| (_dash_sel_col(gt != "" ? gt : g) :&
                      _dash_sel_col(pt != "" ? pt : p))
        }
        if (t == "lowess") {
            _dash_json_get_str(recs[i], "adjust", "_sm_adj")
            adj = strtrim(st_local("_sm_adj"))
            if (adj != "") adj_all = 1
        }
    }
    // A by() graph's panels are its by() groups among its G rows, whatever
    // its plots select: twoway draws a group's panel when no plot has a
    // row in it (test_wp29_truth ER-02), so under by() every G (and Gt)
    // row is marked.
    if (strtrim(by) != "") {
        s = s :| _dash_sel_col(g)
        if (gt != "") s = s :| _dash_sel_col(gt)
    }
    if (adj_all) s = J(st_nobs(), 1, 1)
    st_store(., var, st_data(., var) :| s)
}

// _dash_put_n_obs(gjson, n) -- graph gjson with "n_obs":n, its frame's
// _N, appended as its last key (WP-40 plat:PT-7: lpoly's grid follows
// _N, not the rows exported).  JSON that does not end in } is refused.
string scalar _dash_put_n_obs(string scalar gjson, real scalar n)
{
    string scalar s

    s = strrtrim(gjson)
    if (substr(s, strlen(s), 1) != "}") {
        _error(3498, "graph JSON does not end in }")
    }
    return(substr(s, 1, strlen(s) - 1) + "," + char(34) + "n_obs" +
           char(34) + ":" + strtrim(strofreal(n, "%20.0f")) + "}")
}

end
