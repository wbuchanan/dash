*! dash_parse.mata  v2.0
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
*!   _json_escape(s)
*!       s escaped for a JSON string: the backslash, the double quote and
*!       every byte below 0x20, and the backtick, dollar sign and
*!       apostrophe written as JSON escapes (backslash u 0060, 0024 and
*!       0027), so the result can be expanded inside compound quotes.
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
*!   _dash_strip_prefix()
*!       Reads twoway, tw, two or graph twoway off the front of the
*!       caller's `0' (WP-30 P1.27); sets _pf_kind and _pf_word.
*!
*!   _dash_saving_parse(s, ext)
*!       saving()'s one grammar, as twoway reads it; refuses r(198) or sets
*!       _sv_file, _sv_replace, _sv_asis, _sv_gph, _sv_comma and _sv_img.  Its
*!       internal helper is _dash_saving_split().
*!
*!   _dash_seg_saving(seg)
*!       The value of the last saving() an option list gives, as typed.
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
*!   _dash_note(before, value, after)
*!       Print before + value + after as one note, (note:  ...), in text
*!       colour on Stata's error channel, as twoway prints its notes.
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
*!   _dash_expand_plottype(abbrev, out_macro)
*!       The plot type abbrev names, abbreviated as twoway allows, into
*!       out_macro; "" when it names no type dash draws.
*!
*!   _dash_undrawn_plottype(name)
*!       name, lower case, when it is a twoway plot type dash refuses by
*!       name -- contour, contourline, rpcap, rpspike -- else "".
*!
*!   _dash_kernel_full(word)
*!       The full kernel name, lower case, for a word twoway's kernel()
*!       takes (gau is gaussian, ep and epan epanechnikov); any other
*!       word as given, for the kernel rule to refuse.
*!
*!   _dash_fn_points_json(yvar, n, x0, dx)
*!       A function layer's points as the JSON object
*!       {"x0":..,"dx":..,"y":[..]}: x0 and dx the generator's r(min) and
*!       r(delta), y the first n values of yvar, each %24.17g, a missing
*!       value null.
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
*!       one-line graph's, or each named graph's $dash_fpts_<name> -- or a
*!       bare "}" when there are none; points that are not dash's are
*!       skipped with a note.
*!
*!   _dash_by_scan(scname)
*!       twoway's three by() parse stages over the tail in the string
*!       scalar scname (WP-30 P1.15b): the first copies of rows(), cols(),
*!       holes(), iscale() and imargin(), whether each may go to -syntax-,
*!       and the first leftover word in typed order, into _byg_* locals.
*!
*!   _dash_by_clamp(scname, limit)
*!       Rewrites, in the tail held by the string scalar scname, the first
*!       copy of rows() or cols() above limit to limit (the by_groups
*!       limit), and names the options changed in the local _byg_clamped.
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
*!   _dash_stylelist_keys()
*!       The style options read as stylelists across an expanded varlist.
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
*!   _dash_stylelist_blank(raw, n)
*!       The first quoted blank element among the n used ones, or 0.
*!
*!   _dash_stylelist_probe(tok)
*!       name(x) for an option word whose value is only empty quotes.
*!
*!   _dash_stylelist_locals(raw, stub)
*!       A stylelist's elements as the caller's locals <stub>n, t<j>, q<j>.
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
*!   _dash_kernel_clash(opts, ptype)
*!       "one" for two kernel options, "old" for one beside kernel(), as
*!       twoway refuses them on lpoly, lpolyci and kdensity; else "".
*!
*!   _dash_kernel_flag(unk, ptype)
*!       A kernel written as an option of its own (gau, epan2 ...) on
*!       lpoly, lpolyci or kdensity, read as kernel(<name>): the full
*!       name into the caller's local _kf_name, unk less it into _kf_rest.
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
*!   _dash_split_segs(input)
*!       Split the raw command line into plot segments, into the caller's
*!       locals _n_segs, _seg_1 .. _seg_N (each with its plot type),
*!       _graph_opts_raw and _graph_qual_raw.
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
*!   _dash_extract_filters(filter_out, cmd_out)
*!       Every filter() in the caller's `0': the groups, joined with
*!       " || ", into the local filter_out, and `0' without them into
*!       cmd_out.
*!
*!   _dash_filter_refusal(filter, registry, vars_out)
*!       "" when every filter() group names a variable and only registered
*!       exclude() names, the variables then in vars_out; else the refusal.
*!
*!   _dash_link_refusal(link, registry)
*!       "" when link() is _all alone or names only registered graphs,
*!       else the refusal.
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
*!       dash_json_<name>, dash_spec_<name>, dash_fpts_<name>,
*!       dash_kpi_<name> and dash_kpi_<name>__<field> for each field
*!       _dash_kpi_fields() lists.
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
*!   _dash_reflines_positions(gjson)
*!       The reference-line positions of one graph's JSON: the tokens of
*!       every copy of xline(), yline(), xline2() and yline2() (WP-30
*!       P1.21a), for dash.ado's _dash_reflines_of.
*!
*!   _dash_computed_cells(gjson, nobs, bygroups, types)
*!       -1 unless every plot of gjson is in types; else the cells its
*!       computed layers draw (GAPS2 G3).  _dash_computed_plot_cells()
*!       (120,000, the bound on every computed layer this does not count
*!       exactly) and _dash_filter_excludes(group) (the exclude() names of
*!       one filter() group, factored out of _dash_filter_refusal) are its
*!       own internal helpers, called by no other program directly.
*!
*!   _dash_graph_touched(gname, gjson, filter, link, csv)
*!       1 when a filter, link(), csv or hover() reaches gname's rows
*!       (GAPS2 G3); 0 when only its own computed output is drawn.
*!
*!   _dash_qual_cols_in(gjson)
*!       The distinct qual_col/qual_col_total values named in gjson,
*!       blank-separated (GAPS2 G3).
*!
*!   _dash_route_axis2(opts)
*!       opts with each x/y title, label, tick, line and scale option's
*!       axis(2) rewritten as ytitle2()/ylabel2()/ytick2()/yline2()/
*!       yscale2() (x too), an axis(1) word dropped and twoway's plurals
*!       renamed; every form twoway refuses is left as typed (WP-28 B3,
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
*!       string date functions, never Stata code.
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
*!       title or region; the region's helper is _dash_subreq_region);
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
*! Version: 0.1.0  09oct2026

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
string scalar _json_escape(string scalar s) {
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
// quotes, compound or simple.  The text is escaped by _json_escape(), which
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
    st_local("_dash_jsv", _json_escape(t))
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
// escaped by _json_escape().
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
        out = out + (n ? "," : "") + char(34) + _json_escape(p) + char(34)
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
real scalar _is_utf8(string scalar s) {
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
// _dash_strip_prefix, _dash_saving_split, _dash_saving_parse,
// _dash_seg_saving, _dash_launch_quote and _dash_launch_warn.  Every one
// reads its text by value (st_local, never macro text) and is linear in
// the length of what it reads.
// ============================================================

// _dash_strip_prefix() -- reads twoway's own command words off the front
// of the caller's `0'.  twoway takes `twoway', `tw' and `two', and
// `graph'/`gr' followed by `tw' to `twoway' (measured, StataNow 19.5);
// Stata refuses `twow', `twowa', `gra', `grap' and a capitalised spelling
// with r(199), "command twow is unrecognized", and a second prefix word
// with r(198), "two is not a twoway plot type".  Sets the caller's locals
// _pf_kind ("", "strip", "unrec" or "twice") and _pf_word; on "strip" the
// rest of the command is written back to `0'.  Only whole words from a
// closed list match; the one regex is anchored at the start.
void _dash_strip_prefix()
{
    string scalar    s, w1, w2, rest, t, kind, word
    string rowvector nine

    nine = ("twoway", "tw", "two", "twow", "twowa", "graph", "gr", "gra", "grap")
    s    = st_local("0")
    kind = ""
    word = ""
    rest = ""
    w1   = (ustrregexm(s, "^[a-zA-Z][a-zA-Z0-9_]*") ? ustrregexs(0) : "")
    if (anyof(("twoway", "tw", "two"), w1)) {
        kind = "strip"
        rest = substr(s, strlen(w1) + 1, .)
    }
    else if (anyof(("graph", "gr"), w1)) {
        t  = substr(s, strlen(w1) + 1, .)
        w2 = (ustrregexm(t, "^[ \t]+([a-zA-Z][a-zA-Z0-9_]*)") ? ustrregexs(1) : "")
        if (anyof(("tw", "two", "twow", "twowa", "twoway"), w2)) {
            kind = "strip"
            rest = substr(t, strpos(t, w2) + strlen(w2), .)
        }
    }
    else if (anyof(("twow", "twowa", "gra", "grap"), w1) |
             (w1 != strlower(w1) & anyof(nine, strlower(w1)))) {
        kind = "unrec"
        word = w1
    }
    if (kind == "strip") {
        t = (ustrregexm(rest, "^[ \t]*([a-zA-Z][a-zA-Z0-9_]*)") ? ustrregexs(1) : "")
        if (anyof(nine, t)) {
            kind = "twice"
            word = t
        }
        else st_local("0", rest)
    }
    st_local("_pf_kind", kind)
    st_local("_pf_word", word)
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
    p    = _first_comma_pos(s)
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

    pos = _first_comma_pos(seg)
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
    if (!_is_utf8(s)) {
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
real scalar _dash_layout_scan(string scalar layout, string scalar names) {
    string scalar s, ch, d1, d2
    real scalar   n, i, j, k, npair, big, allpos, maxr, maxc, r, c, st

    names = ""
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
    string rowvector reg, nms, toks, seen
    real scalar      i, eq

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
    if (missing(_dash_layout_scan(s, names))) return(form)
    nms = tokens(names)
    for (i = 1; i <= cols(nms); i++) {
        if (!anyof(reg, nms[i])) return("layout() name '" + nms[i] + "' not found in registry.")
        // Placed twice, it kept its last place without a word.
        if (i > 1) {
            if (anyof(nms[|1 \ i - 1|], nms[i])) {
                return("layout() places '" + nms[i] + "' more than once.")
            }
        }
    }
    return("")
}



// ============================================================
// 2. PLOT-TYPE ABBREVIATION EXPANSION
// ============================================================

string scalar _expand_plottype_str(string scalar name) {
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
        ("pcarrowi","pcarrowi")
    // pccapsym and pcarrowi (WP-22): twoway takes neither by any shorter
    // name -- measured 23sep2026, pc .. pccapsy and pcarr, pcarro are "not
    // a twoway plot type", and pcarrow is its own type -- so the minimum
    // is the full name.  pcarrow still wins "pcarrow": pcarrowi's
    // minimum is eight letters.

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

void _dash_expand_plottype(string scalar abbrev, string scalar out_macro) {
    st_local(out_macro, _expand_plottype_str(strlower(strtrim(abbrev))))
}


// ============================================================
// 2b. TWOWAY PLOT TYPES DASH DOES NOT DRAW
// ============================================================
//
// contour and contourline are twoway plot types (graph_twoway.sthlp) that
// draw a surface interpolated over a grid of z values -- a data model no
// dash plot has (twoway builds them on zyx2view_g, measured from the .gph).
// rpcap and rpspike (y ylow yhigh x, a range drawn with a point on it)
// are twoway plot types in StataNow 19.5 that dash does not draw either.
// dash.ado refuses each by name, with what to use instead, rather than as
// an unrecognised plot type (WP-22 TR-22.1, BR-22.1).  twoway takes no
// abbreviation of any of them -- measured 23sep2026: cont .. contou,
// contourl .. contourlin, rpc .. rpca and rpsp .. rpspik are "not a twoway
// plot type", and con is connected -- so only the full names match.
// Returns the name, lower case, or "".
string scalar _dash_undrawn_plottype(string scalar name) {
    string scalar s

    s = strlower(strtrim(name))
    if (anyof(("contour", "contourline", "rpcap", "rpspike"), s)) {
        return(s)
    }
    return("")
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
            rec = rec + "," + char(34) + _json_escape(lab) + char(34) + "," + clk
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
real scalar _first_comma_pos(string scalar input) {
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
    st_local(out_macro, strofreal(_first_comma_pos(input)))
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
void _dash_split_segs(string scalar input) {
    real   scalar  i, len, depth, in_dq, in_cq, c_code, nxt, p
    real   scalar  seg_start, n_segs
    string scalar  piece
    string vector  pieces, segs
    string scalar  graph_opts_raw, graph_qual

    input  = strtrim(input)
    len    = strlen(input)
    pieces = J(1, 0, "")
    segs   = J(1, 0, "")
    graph_opts_raw = ""
    graph_qual     = ""

    if (len == 0) {
        errprintf("dash: empty plot specification.\n")
        exit(198)
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
    if (depth != 0) {
        errprintf("dash: unbalanced parentheses in the plot specification.\n")
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
    if (n_segs == 0) {
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
    string scalar seg_text, stray, qword, go

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

            // Text between top-level groups, which twoway rejects --
            // `(a) junk (b)' and `(a) | (b)' are r(198) there; dash
            // discarded `junk' and skipped a single `|', rc 0.  Report the
            // whole word, not the one character the scan happened to stop
            // on.  A bare plot after a group needs `||' before it, as in
            // twoway: `(a) || line y x'.
            stray = substr(s, i, .)
            if (strpos(stray, " ") > 0) {
                stray = substr(stray, 1, strpos(stray, " ") - 1)
            }
            errprintf("dash: unexpected text between plot groups: '%s'\n",
                      stray)
            errprintf(
              "      Each plot must be its own parenthesised group.\n")
            exit(198)
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
    // JSON and value labels never reach the Python renderer.
    keys    = (char(34)+"yvar"+char(34)+":",   char(34)+"xvar"+char(34)+":",  char(34)+"var"+char(34)+":",
               char(34)+"yvar1"+char(34)+":", char(34)+"yvar2"+char(34)+":",
               char(34)+"y1var"+char(34)+":", char(34)+"x1var"+char(34)+":", char(34)+"y2var"+char(34)+":", char(34)+"x2var"+char(34)+":",
               char(34)+"mlabel"+char(34)+":",
               char(34)+"mlabvposition"+char(34)+":",
               char(34)+"colorvar"+char(34)+":",
               char(34)+"wexp"+char(34)+":")
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
// is read the way _dash_graph_touched reads it -- _dash_json_get_str: the
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

    _dash_qual_tab  = asarray_create("string", 3)
    _dash_qual_list = J(0, 3, "")
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

    if (strtrim(ifx) == "" & strtrim(inx) == "") return("")
    why = _dash_qual_refusal(ifx, inx)
    if (why != "") {
        st_local(errmacro, why)
        return("")
    }
    if (!name_them) return("")
    key = (ifx, inx, order)
    if (asarray_contains(_dash_qual_tab, key)) {
        return("__dashq" + strofreal(asarray(_dash_qual_tab, key)))
    }
    if (rows(_dash_qual_list) >= 99999) {
        st_local(errmacro, "the dashboard holds more distinct qualifiers than dash evaluates (99,999)")
        return("")
    }
    _dash_qual_list = _dash_qual_list \ key
    k = rows(_dash_qual_list)
    asarray(_dash_qual_tab, key, k)
    return("__dashq" + strofreal(k))
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

    _dash_sort_list = J(0, 1, "")
}

// _dash_sort_scan(json) -- add every "sortvars" value of json to the
// table, each once, in the order first met (read as _dash_qual_cols_in
// reads its keys: the value up to the next double quote).  Sets the
// caller's local _ds_bad to the first value holding a token that is not a
// Stata name, and leaves it alone otherwise.
void _dash_sort_scan(string scalar json)
{
    external string colvector _dash_sort_list
    string scalar    needle, tail, val
    string rowvector t
    real scalar      pos, vstart, vend, i, ok

    if (rows(_dash_sort_list) == 0 & cols(_dash_sort_list) == 0) {
        _dash_sort_list = J(0, 1, "")
    }
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
        else if (!anyof(_dash_sort_list, val)) {
            _dash_sort_list = _dash_sort_list \ val
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
    real scalar k

    if (rows(_dash_sort_list) == 0 & cols(_dash_sort_list) == 0) {
        _dash_sort_list = J(0, 1, "")
    }
    st_local("_ds_n", strofreal(rows(_dash_sort_list)))
    for (k = 1; k <= rows(_dash_sort_list); k++) {
        st_local("_ds_v" + strofreal(k), _dash_sort_list[k])
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

    _dash_tsop_list = J(0, 1, "")
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
    real rowvector   b
    real scalar      n, i, e, k, v, ve, from, m, cap, ix
    string scalar    tok, val, shown
    string rowvector part, keys

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
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
            if (_dash_tsop_list[k] == val) {
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
            _dash_tsop_list = _dash_tsop_list \ val
            ix = rows(_dash_tsop_list)
        }
        if (m + 2 > cap) {
            part = part, J(1, cap, "")
            cap  = 2 * cap
        }
        part[++m] = substr(json, from, v - from)
        part[++m] = char(34) + "__dasht" + strofreal(ix) + char(34)
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
    real scalar k

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
    st_local("_dts_n", strofreal(rows(_dash_tsop_list)))
    for (k = 1; k <= rows(_dash_tsop_list); k++) {
        st_local("_dts_e" + strofreal(k), _dash_tsop_list[k])
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
// _json_escape.  The weight columns __dashw<k> of _dash_wexp_rewrite
// follow, {"expr":"price+1","label":"price+1"} (WP-31 A5).
string scalar _dash_tsop_meta(string scalar fmtmacro)
{
    external string colvector _dash_tsop_list
    external string colvector _dash_wexp_list
    real scalar   k, dot
    string scalar e, base, lab, out, fmt, nm, q

    if (rows(_dash_tsop_list) == 0 & cols(_dash_tsop_list) == 0) {
        _dash_tsop_list = J(0, 1, "")
    }
    q   = char(34)
    out = ""
    fmt = ""
    for (k = 1; k <= rows(_dash_tsop_list); k++) {
        e    = _dash_tsop_list[k]
        dot  = strpos(e, ".")
        base = substr(e, dot + 1, .)
        nm   = "__dasht" + strofreal(k)
        lab  = (_st_varindex(base, 0) < . ? st_varlabel(base) : "")
        lab  = (lab != "" ? lab + ", " + substr(e, 1, dot - 1) : e)
        out  = out + (k > 1 ? "," : "") + q + nm + q + ":{" + q + "expr" + q +
               ":" + q + _json_escape(e) + q + "," + q + "label" + q + ":" +
               q + _json_escape(lab) + q + "}"
        if (_st_varindex(base, 0) < .) {
            fmt = fmt + (fmt != "" ? "," : "") + q + nm + q + ":" + q +
                  _json_escape(st_varformat(base)) + q
        }
    }
    // The weight columns (WP-31 A5): the expression as typed, which is
    // also the text a note shows for the column.
    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
    for (k = 1; k <= rows(_dash_wexp_list); k++) {
        e   = _dash_wexp_list[k]
        nm  = "__dashw" + strofreal(k)
        out = out + (out != "" ? "," : "") + q + nm + q + ":{" + q + "expr" +
              q + ":" + q + _json_escape(e) + q + "," + q + "label" + q +
              ":" + q + _json_escape(e) + q + "}"
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

    _dash_wexp_list = J(0, 1, "")
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
    real rowvector   b
    real scalar      n, i, e, k, v, ve, from, m, cap, ix
    string scalar    tok, val, shown
    string rowvector part

    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
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
            if (_dash_wexp_list[k] == val) {
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
            _dash_wexp_list = _dash_wexp_list \ val
            ix = rows(_dash_wexp_list)
        }
        if (m + 2 > cap) {
            part = part, J(1, cap, "")
            cap  = 2 * cap
        }
        part[++m] = substr(json, from, v - from)
        part[++m] = char(34) + "__dashw" + strofreal(ix) + char(34)
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
    real scalar k

    if (rows(_dash_wexp_list) == 0 & cols(_dash_wexp_list) == 0) {
        _dash_wexp_list = J(0, 1, "")
    }
    st_local("_dwx_n", strofreal(rows(_dash_wexp_list)))
    for (k = 1; k <= rows(_dash_wexp_list); k++) {
        st_local("_dwx_e" + strofreal(k), _dash_wexp_list[k])
    }
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

    c = _first_comma_pos(group)
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
    string scalar    v
    real scalar      g, k

    st_local(vars_out, "")
    groups = _dash_filter_split(filter, 1)
    reg    = tokens(registry)
    for (g = 1; g <= cols(groups); g++) {
        // Split as the renderer splits it, quotes kept: tokens() took
        // exclude("g1") for g1, and the renderer, reading "g1", built no
        // widget, rc 0 (measured 24sep2026; JSE-56).  _dash_filter_excludes
        // (WP-28 G3) is the one reader of a group's exclude() names, so
        // this refusal and _dash_graph_touched's reading cannot drift.
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
string scalar _dash_link_refusal(string scalar link, string scalar registry) {
    string rowvector words, reg
    real scalar      k

    if (link == "_all") return("")
    words = _dash_blank_words(link)
    reg   = tokens(registry)
    for (k = 1; k <= cols(words); k++) {
        // _all links every graph, so beside names it is a contradiction.
        if (words[k] == "_all") {
            return("link(_all) links every graph; give it alone, or name the graphs to link.")
        }
        if (!anyof(reg, words[k])) {
            return("link() name '" + words[k] + "' not found in registry.")
        }
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
            c     = _first_comma_pos(grp)
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
// bgcolor(), update(), and its own if and in.  dash.ado's _dash_kpi writes
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
            "bg", "upd", "if", "in"))
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
// dash_json_<name> and dash_spec_<name>, a function graph's points
// dash_fpts_<name> (WP-29 P0.6: replacing or dropping the graph drops its
// points with it), and a KPI's marker dash_kpi_<name> and its fields
// dash_kpi_<name>__<field> (_dash_kpi_fields).  Only the ones Stata holds
// are returned; an empty field is no global at all.
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
    own = ("dash_json_" + nm, "dash_spec_" + nm, "dash_fpts_" + nm, "dash_tu_" + nm,
           "dash_kpi_" + nm)
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
// not allowed", r(198).  Options are case-sensitive and NAMe() admits the
// spellings nam and name only, so only those count: NAME() is an option
// dash does not know, and "name(x)" written inside another option's
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
    return(anyof(names, "name") | anyof(names, "nam"))
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

    pos = _first_comma_pos(seg)
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

// _dash_fn_points_json(yvar, n, x0, dx) -- a function layer's points, as
// twoway__function_gen made them, as one JSON object (WP-29 P0.6):
// {"x0":<x0>,"dx":<dx>,"y":[<y1>,...,<yn>]}.  x0 and dx are the
// generator's r(min) and r(delta), so x is x0 + dx*(i-1) exactly as the
// generator built it (the renderers rebuild it so, bit for bit; section 04
// E7); y is the first n values of yvar in the generator's order, missing
// as null.  Every number is _dash_json_number17's, so the object holds no
// character but digits, . + - e E, the letters of null, x0, dx and y, and
// " : , { } [ ] -- _dash_fn_spec_tail checks exactly that.
string scalar _dash_fn_points_json(string scalar yvar, real scalar n,
                                   real scalar x0, real scalar dx)
{
    string scalar q
    string colvector y

    q = char(34)
    y = _dash_json_number17(st_data((1, n), yvar))
    return("{" + q + "x0" + q + ":" + _dash_json_number17(x0) + "," +
           q + "dx" + q + ":" + _dash_json_number17(dx) + "," +
           q + "y" + q + ":[" + invtokens(y', ",") + "]}")
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
// x d y " : , { } [ ] (an ascii() lookup).  A global the user set by hand
// to anything else -- }],"graphs":[ among them -- cannot reach the spec.
real scalar _dash_fn_points_ok(string scalar txt)
{
    real rowvector ok, b
    string scalar  allowed

    if (strlen(txt) < 2) return(0)
    if (substr(txt, 1, 1) != "{" | substr(txt, strlen(txt), 1) != "}") return(0)
    allowed = "0123456789.+-eEnulxdy" + char(34) + ":,{}[]"
    ok = J(1, 256, 0)
    b  = ascii(allowed)
    ok[b :+ 1] = J(1, cols(b), 1)
    b = ascii(txt)
    return(all(ok[b :+ 1]))
}

// _dash_fn_spec_tail(path, names, sc) -- close the spec file at path with
// the function points beside the graphs (WP-29 P0.6).
//
// The writers leave the spec's last } off and call this after closing the
// file, so the points -- up to c(macrolen) characters a graph -- never
// travel through a macro concatenation (a local past c(macrolen) is an
// uncapturable r(920), and st_global() past it truncates in silence;
// section 04 E6).  With sc != "", the string scalar sc holds the one-line
// graph's table and is the single entry, keyed "" (the graph has no name).
// Otherwise there is one entry "<name>":$dash_fpts_<name> for each word of
// names whose global is not empty.  An entry that is not dash's
// (_dash_fn_points_ok) is skipped with a note; the renderers then draw that
// layer as a spec without points, and name what they cannot evaluate
// (WP-30 P1.22).  Appends ,"function_points":{<entries>}} or,
// with no entry, the bare }.
void _dash_fn_spec_tail(string scalar path, string scalar names,
                        string scalar sc)
{
    string rowvector nm
    string scalar    q, out, txt
    real scalar      i, fh

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
            txt = st_global("dash_fpts_" + nm[i])
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
    fh = fopen(path, "a")
    if (out == "") fwrite(fh, "}")
    else fwrite(fh, "," + q + "function_points" + q + ":{" + out + "}}")
    fclose(fh)
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
// of them: the style options (P1.1a), then the value lists mlabel jitter
// base barwidth (P1.1b), then the named styles pstyle lstyle clstyle mstyle
// mlstyle astyle alstyle bstyle blstyle (P1.14a; p() is one name and is
// not split), dstyle dlstyle bmlinestyle (P1.14b, kept and named) and
// mlabtextstyle (P1.24), then connect cmissing (P1.8a), which
// _dash_connect_opt canonicalises before the per-y writer splits them.
string scalar _dash_stylelist_keys()
{
    return("mcolor msymbol msize msangle mfcolor mlcolor mlwidth " +
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
// a word of ... alone is the repeat.
// Nothing else is split: ..blue, red...blue, red=blue and (red) stay one
// element each, as twoway reads them.  Linear in the length of raw.
string matrix _dash_stylelist_elems(string scalar raw)
{
    string rowvector toks
    string matrix    out
    string scalar    t, stem, rep
    real scalar      i, n, k, len, p, in_dq, in_cq, q

    toks = _dash_rep_toks(raw, 0)
    n    = cols(toks)
    out  = J(2, 2 * n, "")
    k    = 0
    for (i = 1; i <= n; i++) {
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
        }
        k++
        out[1, k] = stem
        out[2, k] = (q ? "1" : "0")
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
// test/fixtures/connect_truth.json measures them (its S block): exact
// and case-sensitive (L is ascending, l direct; N and j are unknown),
// the long names also by the abbreviations the fixture shows taken (dir,
// asc, asce, stair, stairs).  A fixed table read by value; O(len(e)).
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
    if (t == "l" | t == "line" | t == "d" | t == "c" | t == "connected") return("direct")
    if (n >= 3 & n <= 6 & t == substr("direct", 1, n)) return("direct")
    if (t == "L" | t == "a") return("ascending")
    if (n >= 3 & n <= 9 & t == substr("ascending", 1, n)) return("ascending")
    if (t == "J" | t == "s") return("stairstep")
    if (n >= 5 & n <= 9 & t == substr("stairstep", 1, n)) return("stairstep")
    if (t == "u" | t == "upstairstep") return("stepstair")
    if (n >= 4 & n <= 9 & t == substr("stepstair", 1, n)) return("stepstair")
    if (t == "n" | t == "i" | t == "none") return("none")
    return("?")
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
    if (anyof(("title", "subtitle", "note", "caption", "xtitle", "ytitle",
               "xtitle2", "ytitle2", "t1title", "t2title", "b1title",
               "b2title", "l1title", "l2title", "r1title", "r2title",
               "title2", "subtitle2", "ztitle", "ttitle", "ttitle2"), k)) return("T")
    if (anyof(("xlabel", "ylabel", "xlabel2", "ylabel2", "xtick", "ytick",
               "xtick2", "ytick2", "xmtick", "ymtick", "xmlabel", "ymlabel",
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
               // GAPS2 X2: colorvarminmax, now declared, is refused a
               // second time as twoway refuses it.  colorlevels() is NOT
               // here: twoway takes it twice (measured 26sep2026).
               "colorvarminmax",
               // WP-31 C2: mwidth, now declared, is taken once on rbar
               // and histogram (measured 13oct2026).
               "mwidth"), k)) return(1)
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
    t = t \ ("atobs",        "atobs",        "ato",       "0", fits,        "0", "")
    t = t \ ("xlog",         "xlog",         "xlog",      "0", fits,        "0", "")
    t = t \ ("baroffset",    "baroffset",    "baroff",    "1", "rbar",      "0", "")
    t = t \ ("biweight",     "biweight",     "bi",        "0", kerns,       "0", "")
    t = t \ ("cosine",       "cosine",       "cos",       "0", kerns,       "0", "")
    t = t \ ("epan2",        "epan2",        "epan2",     "0", kerns,       "0", "")
    t = t \ ("epanechnikov", "epanechnikov", "ep",        "0", kerns,       "0", "")
    t = t \ ("gaussian",     "gaussian",     "gau",       "0", kerns,       "0", "")
    t = t \ ("parzen",       "parzen",       "par",       "0", kerns,       "0", "")
    t = t \ ("rectangle",    "rectangle",    "rec",       "0", kerns,       "0", "")
    t = t \ ("triangle",     "triangle",     "tri",       "0", kerns,       "0", "")
    t = t \ ("boundary",     "boundary",     "boundary",  "0", "kdensity",  "0", "")
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
    // 4. pwidth() a positive number
    if (hasp) {
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

    p = _first_comma_pos(v)
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
            "mlabel", "mlabels", "mlabel", "3", "3", ""       \
            "tick",   "ticks",   "tick",   "4", "4", "tick2"  \
            "mtick",  "mticks",  "mtick",  "3", "5", ""       \
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
//   any other axis, an mlabel or mtick on axis 2, a second axis word, an
//       axis word in capitals and a second comma: left as typed, for
//       _dash_axreq_check to refuse in twoway's words (or, for ymlabel()
//       and ymtick() on axis 2, for the note).
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
        else if (n == 2 & fam[r, 6] != "") dn = d + fam[r, 6]
        else continue
        toks[i] = dn + "(" + (scale ? rest :
                  body + (rest == "" ? "" : ", " + rest)) + ")"
        any = 1
    }
    // Nothing routed: the list exactly as typed, spacing and all (and no
    // join, which the 10,000-copy exhaustion case TP-14e times).
    if (!any) return(opts)
    for (i = 1; i <= cols(toks); i++) out = out + (i > 1 ? " " : "") + toks[i]
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
    string scalar    d, v, body, dcw, badw, sm, lb, lb2, ls2, lnone
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
            if (_dash_so_resolve(words, J(1, cols(words), 1), "axscale",
                                 snames, sm, sat) == 0) sm = ""
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
// evaluated.  S56's ttext() reads its position with it too.
real scalar _dash_tdate_value(string scalar tok, string scalar unit,
                              real scalar val)
{
    string scalar  t, ok
    real scalar    v, i
    real rowvector w

    t = strtrim(tok)
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
    ok = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz.+-*/@=_"
    for (i = 1; i <= strlen(t); i++) {
        if (!strpos(ok, substr(t, i, 1))) return(3)
    }
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
            k = _dash_tdate_value(a, unit, v)
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
        p = _first_comma_pos(rest)
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
        t   = tokens(seg)
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
        t = tokens(_dash_rep_value(w[i]))
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
                  "orientation", "orient", "4", "a", "1", "" \
                  "r1title", "r1", "5", "r", "1", "" \
                  "r2title", "r2", "5", "r", "1", "" \
                  "l1title", "l1", "5", "r", "1", "")
        t = t \ ("l2title", "l2", "5", "r", "1", "" \
                  "t1title", "t1", "5", "r", "1", "" \
                  "t2title", "t2", "5", "r", "1", "" \
                  "b1title", "b1", "5", "r", "1", "" \
                  "b2title", "b2", "5", "r", "1", "" \
                  "note", "note", "5", "r", "1", "")
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
    if (cat == "T") return("textbox")
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
        else if (strlen(nm) >= 4 & substr("zlabel", 1, strlen(nm)) == nm) {
            kind = "zlabel"
            sub  = ""
            if (_dash_rep_split(v, body, sub)) {
                if (_dash_rep_split(sub, b2, s2)) sub = b2
            }
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
    real scalar      rc, at, i, j, k, c, q, hasp, hass

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
        if (lastpos != "" & !anyof(("0", "1", "2", "3", "4", "5", "6", "7",
                                    "8", "9", "10", "11", "12"), lastpos)) {
            _dash_note("named style ", lastpos,
                       " not found in class clockdir, default attributes used")
        }
        if (lastring != "" & !_dash_so_isnum(lastring, 0)) {
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
        _dash_subreq_drop("region:graphregion")
        _dash_subreq_drop("region:plotregion")
        return(0)
    }
    if (kind == "zlabel") {
        for (i = 1; i <= rows(_dash_subreq); i++) {
            if (_dash_subreq[i, 1] != "zlabel") continue
            toks = _dash_rep_toks(_dash_subreq[i, 4], 1)
            if (cols(toks) == 0) continue
            if (_dash_so_resolve(toks, J(1, cols(toks), 1), "axlabel",
                                 names, msg, at)) {
                _dash_say("err", "", msg, "")
                _dash_subreq_clear()
                return(198)
            }
        }
        _dash_subreq_drop("zlabel")
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
        }
        _dash_subreq_clear()
        return(0)
    }
    return(0)
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
    string rowvector a, an, drop
    string scalar    out, nm, base, pre, rw, tn
    real rowvector   alive
    real scalar      i, j, k, has

    a     = w1
    an    = n1
    alive = J(1, cols(a), 1)
    for (j = 1; j <= cols(w2); j++) {
        nm = n2[j]
        if (nm == "margin" | nm == "imargin") continue
        if (nm == "") {
            tn = _dash_rep_optname(w2[j])
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
    for (j = 1; j <= cols(w2); j++) {
        out = out + (out == "" ? "" : " ") + _dash_rep_region_word(w2[j], n2[j])
    }
    return(out)
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
    real scalar      c1, c2, has2, suf, pre, add, a1, keep

    cat = _dash_rep_cat(key)
    if (cat == "F") return(strtrim(v1) != "" ? v1 : v2)
    if (cat == "R" | strtrim(v1) == "") return(v2)
    if (strtrim(v2) == "") return(v1)
    // Each copy kept apart by a record separator; _dash_at_lex splits
    // only outside quotes (WP-30 P1.10).
    if (cat == "A") return(v1 + char(30) + v2)
    if (cat == "H") return(strtrim(v1) + " " + strtrim(v2))
    if (cat == "X") return(v1 + ", " + v2)
    if (cat == "I" | cat == "S") {
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
    if (suf & has2)       body = strtrim(b1) + " " + strtrim(b2)
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
// caller's locals _at_k (copies) and _at_n (records).  Returns 0.  Reads
// and writes by value only; 100,000 one-point copies take well under a
// second (AT-04b).
real scalar _dash_at_parse(string scalar raw, real scalar datesok)
{
    external string matrix _dash_at_R, _dash_at_C
    real colvector st, ln, kd, cp, os, ol
    real rowvector bb
    string scalar  y, x, line, js, bare, ks
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
                // _json_escape() only where a byte needs it.
                bb = ascii(line)
                if (cols(bb)) {
                    if (any(bb :< 32 :| bb :== 34 :| bb :== 36 :| bb :== 39 :|
                            bb :== 92 :| bb :== 96)) line = _json_escape(line)
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
// (style/compass2dir-*.style, measured: test/fixtures/
// added_text_truth.json _meta.compass), "" for a name twoway notes and
// draws east.  Lower case, as Stata's style names are.
string scalar _dash_at_place(string scalar p)
{
    string matrix T
    real scalar   i

    T = ("n", "n" \ "north", "n" \ "12", "n" \ "t", "n" \ "top", "n" \
         "1", "ne" \ "2", "ne" \ "ne", "ne" \ "neast", "ne" \
         "3", "e" \ "e", "e" \ "east", "e" \ "r", "e" \ "right", "e" \
         "4", "se" \ "5", "se" \ "se", "se" \ "seast", "se" \
         "6", "s" \ "s", "s" \ "south", "s" \ "b", "s" \ "bottom", "s" \
         "7", "sw" \ "8", "sw" \ "sw", "sw" \ "swest", "sw" \
         "9", "w" \ "w", "w" \ "west", "w" \ "l", "w" \ "left", "w" \
         "10", "nw" \ "11", "nw" \ "nw", "nw" \ "nwest", "nw" \
         "0", "c" \ "c", "c" \ "center", "c")
    for (i = 1; i <= rows(T); i++) {
        if (T[i, 1] == p) return(T[i, 2])
    }
    return("")
}

// _dash_at_orient(o) -- the orientation twoway draws orientation(o) in
// (style/tb_orientstyle-*.style, measured: _meta.orient): horizontal,
// vertical, rvertical or rhorizontal, "" for a name twoway notes and
// draws horizontally.
string scalar _dash_at_orient(string scalar o)
{
    string matrix T
    real scalar   i

    T = ("horizontal", "horizontal" \ "horiz", "horizontal" \
         "vertical", "vertical" \ "vert", "vertical" \
         "rvertical", "rvertical" \ "rvert", "rvertical" \
         "rhorizontal", "rhorizontal" \ "rhoriz", "rhorizontal")
    for (i = 1; i <= rows(T); i++) {
        if (T[i, 1] == o) return(T[i, 2])
    }
    return("")
}

// _dash_at_json(kind, y, x, ya, xa, lines, opts) -- one added_text record:
// {"at_kind":..,"at_y":..,"at_x":..,"at_yaxis":..,"at_xaxis":..,
// "at_lines":[..],"at_opts":".."}.  Numbers in %21.0g; lines already a
// JSON array and opts already _json_escape()d (_dash_at_opts), written as
// they come.  Every key starts at_, so no substring reader of the graph's
// JSON (_dash_json_has_value, _dash_json_first_num) finds one.
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
// size() color() justification() orientation() box or nobox fcolor()
// lcolor() lwidth() margin() placement(), bfcolor() blcolor() blwidth()
// standing in for the plain ones when those are absent and bcolor() for
// both colours when neither is given; _json_escape()d.  orientation()
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
    v = st_local("justification")
    if (v != "") out = out + " justification(" + v + ")"
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
    v = st_local("margin")
    if (v != "") out = out + " margin(" + v + ")"
    p = st_local("placement")
    if (p != "") {
        p = _dash_at_place(p)
        out = out + " placement(" + (p != "" ? p : "e") + ")"
    }
    return(_json_escape(strtrim(out)))
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

// GAPS2 G3 (WP-28 section 08): what the SAVED page embeds is not every
// exported variable times _N -- a graph made only of computed layers
// (histogram, kdensity, the fits and smoothers) that nothing else reaches
// draws its own drawn output, bounded, whatever the row count.  The
// SERVED app is unaffected: _embed_data (dash_render.py) always embeds
// every row.
//
// _dash_json_count_key(s, key, val) -- occurrences of "key":"val..." in s;
// val == "" counts every value of key (as _dash_spec_types_in does for
// "type").  A helper shared by the counters below so they read the spec's
// raw JSON text the same way _dash_spec_types_in and _dash_json_get_str
// do -- no JSON parse, so a title or a qualifier's text can hold anything
// without being mistaken for a key.
real scalar _dash_json_count_key(string scalar s, string scalar key,
                                 string scalar val) {
    string scalar needle
    needle = char(34) + key + char(34) + ":" + char(34) + val +
             (val != "" ? char(34) : "")
    if (strlen(needle) == 0) return(0)
    return((strlen(s) - strlen(subinstr(s, needle, "", .))) / strlen(needle))
}

// 1 when "key":"<non-empty>" is in s (a flag or a value sub-option that
// was actually given: _dash_plot_opts_to_json (dash.ado) writes a key only
// when its s() value is non-empty).
real scalar _dash_json_has_value(string scalar s, string scalar key) {
    string scalar needle
    real scalar   pos
    needle = char(34) + key + char(34) + ":" + char(34)
    pos = strpos(s, needle)
    if (!pos) return(0)
    return(substr(s, pos + strlen(needle), 1) != char(34))
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

// _dash_computed_plot_cells() -- one bound on every computed layer except
// histogram and lowess, which _dash_computed_cells counts exactly.
// Derivation (dash.ado's option caps at _dash_option_rules, ~1866, and
// the renderer's own grids):
//   kdensity, lpoly, lpolyci, lfit family (2 or 4 * n, n <= 10000)  40,000
//   fpfit, fpfitci                      (2 or 4 * _FP_GRID_MAX)    80,000
//   mspline           (2 * ((bands-1)*n + bands), bands<=200, n<=300) 119,800
//   mband                               (2 * bands, bands <= 200)      400
// 120,000 bounds every one of these; test/test_embedded_cells.py::
// TestTheTwoLanguagesAgree::test_the_constant_bounds_every_computed_layer
// re-derives the bound from dash.ado's own caps.
real scalar _dash_computed_plot_cells() {
    return(120000)
}

// -1 unless every plot type in gjson is one of `types' (_dash_spec_types_in);
// else the cells this graph's computed layers draw: a lowess draws 2 per
// observation and never escapes any cap; a histogram draws 4 times its bin
// count -- the data's own count under width()/discrete() with no bin(),
// else the first bin() given, else Stata's default rule
// (max(1, floor(min(sqrt(nobs), 10*log10(nobs))))); every other computed
// type is bounded by _dash_computed_plot_cells().
//
// by() returns -1 (not computed-only): the actual panel count is not
// known before the export, and multiplying the per-panel bound by the
// by_groups LIMIT instead (100 by default) makes even a two-panel
// by(foreign) on a generic computed type -- kdensity, lpoly, lpolyci,
// the fits, mspline, mband, all bounded at 120,000 -- read as
// 12,000,000, over the DEFAULT cells limit on any dataset, however
// small (measured: it refused test_help_claims_6.py's fifty-point lpoly
// grid under by(foreign), which built before this section and must
// still build).  A by()-faceted graph is counted in full instead, as it
// was before this section, until the real panel count is known here.
real scalar _dash_computed_cells(string scalar gjson, real scalar nobs,
                                 real scalar bygroups, string scalar types) {
    real scalar P, L, H, wd, bin_val, bins, cells

    if (_dash_json_has_value(gjson, "by")) return(-1)
    if (!_dash_spec_types_in(gjson, types)) return(-1)

    P = _dash_json_count_key(gjson, "type", "")
    L = _dash_json_count_key(gjson, "type", "lowess")
    H = _dash_json_count_key(gjson, "type", "histogram")

    bin_val = _dash_json_first_num(gjson, "bin")
    // dash.ado's own bin=int,1,1000 option cap keeps a dash-built spec's
    // bin() in range already; this clamp matches the renderer's own
    // map_histogram _MAX_BINS (dash_render.py, ~9907) for a hand-written
    // spec that reached here another way.
    if (bin_val != . & bin_val > 1000) bin_val = 1000
    wd = (bin_val == .) & (_dash_json_has_value(gjson, "width") |
                           _dash_json_has_value(gjson, "discrete"))
    if (bin_val != .) bins = bin_val
    else if (nobs <= 0) bins = 1
    else bins = max((1, floor(min((sqrt(nobs), 10 * log10(nobs))))))

    cells = L * 2 * nobs + H * 4 * (wd ? nobs : bins) +
            (P - L - H) * _dash_computed_plot_cells()
    return(cells)
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
            p = _first_comma_pos(rest)
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

// 1 when a filter, link(), csv or hover() reaches gname's rows: csv holds
// every column of the frame; link(_all) or link() naming gname shares one
// source; hover() is read the way dash.ado reads it (_dash_json_get_str,
// over the graph's own JSON, so a title or qualifier holding the text
// "hover" is never mistaken for the key); and a filter group whose
// exclude() does NOT name gname reaches it (a group with no exclude() at
// all reaches every graph).  0 otherwise -- the graph draws only its own
// computed output, and _dash_computed_cells already bounds that.
real scalar _dash_graph_touched(string scalar gname, string scalar gjson,
                                string scalar filter, string scalar link,
                                string scalar csv) {
    string rowvector groups, excl
    string scalar    hover
    real scalar      g

    if (csv != "") return(1)
    if (link == "_all") return(1)
    if (anyof(_dash_blank_words(link), gname)) return(1)
    _dash_json_get_str(gjson, "hover", "_dgt_hover")
    hover = strtrim(st_local("_dgt_hover"))
    if (hover != "") return(1)
    if (filter != "") {
        groups = _dash_filter_split(filter, 1)
        for (g = 1; g <= cols(groups); g++) {
            excl = _dash_filter_excludes(groups[g])
            if (!anyof(excl, gname)) return(1)
        }
    }
    return(0)
}

// The distinct "qual_col" and "qual_col_total" values named anywhere in
// gjson (a graph's own qualifier, each plot's, and the by() Total panel's),
// blank-separated; "" values are not qualifiers and are skipped.  Read the
// same raw-text way as the counters above.
string scalar _dash_qual_cols_in(string scalar gjson) {
    string rowvector keys
    string scalar    out, needle, tail, val
    real scalar      ki, pos, vstart, vend

    out  = ""
    keys = ("qual_col", "qual_col_total")
    for (ki = 1; ki <= 2; ki++) {
        needle = char(34) + keys[ki] + char(34) + ":" + char(34)
        tail = gjson
        pos = strpos(tail, needle)
        while (pos) {
            vstart = pos + strlen(needle)
            vend = strpos(substr(tail, vstart, .), char(34))
            if (!vend) break
            val = substr(tail, vstart, vend - 1)
            if (val != "" & !strpos(" " + out + " ", " " + val + " ")) {
                out = out + (out == "" ? "" : " ") + val
            }
            tail = substr(tail, vstart + vend, .)
            pos = strpos(tail, needle)
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
// mtick families (axis 2: label2, tick2).  It reads the caller's merged
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
            "x", "scale2", "scale" \ "x", "label2", "label" \
            "x", "tick2", "tick")
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

end
