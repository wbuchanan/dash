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
*!   _dash_text_args(nlead, ntail, optnum)
*!       A program's `0' read by value: its first nlead and last ntail
*!       arguments (dash's own words) into _dash_a1, _dash_a2, ..., their
*!       count into _dash_na, and the one user text between them, less one
*!       pair of enclosing quotes, into _dash_txt.  With optnum, a last
*!       argument that is all digits is taken as one more.
*!
*!   _dash_path_badchar(path)
*!       The byte value of the first shell-hazardous character in path --
*!       the double quote, backtick, dollar sign, semicolon, &, |, <, >,
*!       tab, LF or CR -- or 0.
*!
*!   _dash_check_utf8(s)
*!       Refuses s, r(198), unless it is well-formed UTF-8.
*!
*!   _dash_say(style, before, value, after)
*!       Print before + value + after as one line in SMCL style "err",
*!       "txt" or "res", every character shown as written.
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
*!       name -- contour, contourline, heatmap, rpcap, rpspike -- else "".
*!
*!   _dash_kernel_full(word)
*!       The full kernel name, lower case, for a word twoway's kernel()
*!       takes (gau is gaussian, ep and epan epanechnikov); any other
*!       word as given, for the kernel rule to refuse.
*!
*!   _dash_fn_names(expr, cap)
*!       The names a function expression calls -- each name written
*!       directly before a `(' outside quotes, once, at most cap -- for
*!       dash.ado to ask Stata whether each is a function.
*!
*!   _dash_unbound_cands(raw, cap)
*!       The options of a parser's catch-all whose value -syntax- may not
*!       have bound, into the caller's locals _ru_n, _ru_tok<i>, _ru_nm<i>
*!       and _ru_rc<i> (twoway's code for each, r(109) or r(198)).
*!
*!   _dash_fn_space_call(expr)
*!       The first operand of a function expression written with blanks
*!       before a `(' -- "N <pos> <name>", "T <pos> <name>" (tabs alone)
*!       or "O <pos>" -- or "", for dash.ado to refuse as twoway does.
*!
*!   _dash_rep_scan(opts, unk, cap)
*!       Whether an option list may give an option twice, and its distinct
*!       spellings, into the caller's locals _rp_go, _rp_n, _rp_nm<i> and
*!       _rp_tok<i>.
*!
*!   _dash_rep_keyof(snames)
*!       The option a word read alone set, from the parser's s() names.
*!
*!   _dash_rep_reduce(opts, ptype)
*!       The option list with one copy of each option, as twoway reads a
*!       repeated one (the last copy, or the copies merged); the caller's
*!       local _rp_refuse names a unique option given twice.
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
*!   _dash_rep_merge_locals(key, m1, m2, out)
*!       Two copies of option key, the caller's locals m1 then m2, merged
*!       as twoway merges them, into the caller's local out.
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
*!       dash_json_<name>, dash_spec_<name>, dash_kpi_<name> and
*!       dash_kpi_<name>__<field> for each field _dash_kpi_fields() lists.
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
*!       opts with ytitle(..., axis(2))/xtitle(..., axis(2)) rewritten as
*!       ytitle2()/xtitle2() and an axis(1) word dropped (WP-28 B3).
*!
*!   _dash_axis_pieces(s)
*!       An axis-label option's value split into strings, bare runs and
*!       its sub-option tail, into the caller's locals _ap_n, _ap_tag<i>
*!       and _ap_txt<i> (WP-28 S14, GAPS2 B1).
*!
*! Version: 2.0  24sep2026

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
// Returns the byte value of the first shell-hazardous character in
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
// Bytes rejected: " ` $ ; & | < > and TAB/LF/CR.  Scanning bytes
// rather than characters is deliberate: these are shell metacharacters,
// and a multibyte sequence that happens to contain one of these bytes
// is still dangerous at the shell.  Parentheses are NOT rejected --
// every call site quotes the path, inside which they are literal, and
// rejecting them broke every Windows path under "Program Files (x86)".
// ============================================================
real scalar _dash_path_badchar(string scalar path) {
    real scalar      i, c, n
    real rowvector   bad

    bad = (34, 96, 36, 59, 38, 124, 60, 62, 9, 10, 13)
    n   = strlen(path)
    for (i = 1; i <= n; i++) {
        c = ascii(substr(path, i, 1))
        if (anyof(bad, c)) return(c)
    }
    return(0)
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

    // (full name, minimum abbreviation).  Minimums are MEASURED against real
    // twoway -- see scripts/extract_abbrev_truth.do and
    // test/fixtures/abbrev_truth.json -- except where dash historically
    // accepted something SHORTER, which is kept when it introduces no
    // ambiguity.  Accepting more than twoway does cannot break drop-in parity
    // and it keeps existing dash do-files working.
    //
    // Matching below accepts ANY prefix at least as long as the minimum, the
    // way Stata does, replacing the fixed one-short-form-each table that
    // rejected every other prefix.
    tbl = ("scatter","sc") \
        ("line","li") \
        ("connected","con") \
        ("area","ar") \
        ("bar","ba") \
        ("spike","sp") \
        ("lfit","lfi") \
        ("qfit","qfi") \
        ("lfitci","lfitci") \
        ("qfitci","qfitci") \
        ("lowess","low") \
        ("lpoly","lpo") \
        ("lpolyci","lpolyci") \
        ("fpfit","fp") \
        ("fpfitci","fpfitci") \
        ("histogram","hist") \
        ("kdensity","kde") \
        ("rarea","rarea") \
        ("rbar","rbar") \
        ("rspike","rspike") \
        ("rcap","rcap") \
        ("rline","rl") \
        ("rconnected","rcon") \
        ("dot","dot") \
        ("dropline","dr") \
        ("rcapsym","rcapsym") \
        ("pcspike","pcspike") \
        ("pcarrow","pcarrow") \
        ("pcbarrow","pcbarrow") \
        ("pci","pci") \
        ("pcscatter","pcscatter") \
        ("tsline","tsl") \
        ("tsrline","tsrl") \
        ("mspline","msp") \
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
    // probed (these 40 and the five dash refuses by name) it took each as
    // the one type whose minimum it reaches, or refused it, "s is not a
    // twoway plot type", r(198) -- s, r, pc, rc and every other prefix of
    // two names that reaches neither minimum among them -- which is what
    // dash's "unrecognised plot type" says.  test_parser.cscript P1A-76 and
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
// heatmap (z y x, a grid of rectangles coloured by z), rpcap and rpspike
// (y ylow yhigh x, a range drawn with a point on it) are twoway plot types
// in StataNow 19.5 that dash does not draw either.  dash.ado refuses each
// by name, with what to use instead, rather than as an unrecognised plot
// type (WP-22 TR-22.1, BR-22.1).  twoway takes no abbreviation of any of
// them -- measured 23sep2026: cont .. contou, contourl .. contourlin,
// heat .. heatma, rpc .. rpca and rpsp .. rpspik are "not a twoway plot
// type", and con is connected -- so only the full names match.  Returns
// the name, lower case, or "".
string scalar _dash_undrawn_plottype(string scalar name) {
    string scalar s

    s = strlower(strtrim(name))
    if (anyof(("contour", "contourline", "heatmap", "rpcap", "rpspike"), s)) {
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
// Two things twoway takes are refused here, because they are accidents of
// its implementation rather than its syntax: a numlist range that holds
// one number, which twoway then evaluates as a division (2/2 and -1/-1
// draw at 1, 0/0 is missing, and (1/1) is taken as a clock position); and
// a hexadecimal literal at the top of a double's range (1.0X+3ff), missing
// there.
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

// One coordinate, as twoway reads it -- numlist with missingok, then
// stored as a float: a JSON number; "null" for a missing value (. or .a to
// .z, a number past a double's range, or one past a float's); or "" when it
// is no number at all, twoway's "invalid point".  tok is the token as
// gettoken hands it over, quotes stripped.
string scalar _dash_imm_number(string scalar tok)
{
    string scalar t
    real scalar   v

    t = _dash_imm_trim(tok)
    if (t == ".") return("null")
    if (strlen(t) == 2 & substr(t, 1, 1) == ".") {
        if (_dash_ascii_in(substr(t, 2, 1), 97, 122)) return("null")
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
// Detect whether the input uses:
//   (a) PAREN syntax — first non-whitespace token is "("
//   (b) FLAT  syntax — plot types separated by "||"
//
// PAREN MODE:
//   Collect each top-level parenthesised group as a segment.
//   After all groups, a top-level comma introduces graph-level options.
//   Sets: _n_segs, _seg_1..N, _graph_opts_raw
//
// FLAT MODE:
//   Split the input on "||" tokens at depth 0.
//   The last segment may contain BOTH plot options and graph-level options
//   (both will be parsed together by the Stata syntax program — no need to
//   pre-separate them here).
//   Sets: _n_segs, _seg_1..N, _graph_opts_raw = ""
//
// In both modes each _seg_K includes the plot-type name as its first word.
//
void _dash_split_segs(string scalar input) {
    real   scalar  i, len, depth, in_dq, in_cq, c_code, nxt
    real   scalar  seg_start, n_segs
    string scalar  seg_text, trimmed, stray, qword
    real   scalar  qual_seen, qnext, qual_start, qdepth
    string vector  segs
    string scalar  graph_opts_raw, graph_qual

    trimmed        = strtrim(input)
    len            = strlen(trimmed)
    n_segs         = 0
    segs           = J(1, 0, "")
    graph_opts_raw = ""
    graph_qual     = ""

    if (len == 0) {
        errprintf("dash: empty plot specification.\n")
        exit(198)
    }

    // ---- detect syntax mode ----
    // Skip leading whitespace and check first non-white character.
    real scalar first_non_white
    first_non_white = 0
    for (i = 1; i <= len; i++) {
        c_code = ascii(substr(trimmed, i, 1))
        if (c_code != 32 & c_code != 9) {
            first_non_white = c_code
            break
        }
    }

    // ================================================================
    // PAREN MODE  (first real char is "(")
    // ================================================================
    if (first_non_white == 40) {
        depth    = 0
        in_dq    = 0
        in_cq    = 0
        seg_start = 0
        qual_seen = 0
        qual_start = 0
        qdepth    = 0
        i         = 1

        while (i <= len) {
            // Quoted text is opaque at any depth.
            nxt = _dash_quote_step(trimmed, len, i, in_dq, in_cq)
            if (nxt) {
                i = nxt
                continue
            }

            c_code = ascii(substr(trimmed, i, 1))

            // ---- inside an if/in qualifier written between or after the
            // plot groups ----
            // twoway applies such a qualifier to every plot (measured:
            // `(scatter y x) (line y x) if foreign==1' draws the 22 foreign
            // cars in both), wherever it stands at the top level -- after
            // the last group, or before a `||' -- and allows one `if' and
            // one `in' in all ("multiple global if's not allowed").  It is
            // collected here, whole, into graph_qual, and _dash_plot reads
            // it with -syntax- as the graph's own qualifier.  This scanner
            // used to walk past it and throw it away, so every observation
            // was drawn, in silence -- and a parenthesis in it,
            // `if inlist(rep78,3,4)', opened a plot group.  Inside the
            // qualifier a parenthesis is the expression's; it ends at a
            // comma or a `||' outside its parentheses (and outside quotes,
            // which the step above skips), or at the end.  A plot group
            // written after it without `||' stays part of its text, where
            // -syntax- refuses it with twoway's own "invalid '('".
            if (qual_seen) {
                if (c_code == 40) {
                    qdepth++
                }
                else if (c_code == 41) {
                    if (qdepth == 0) {
                        errprintf("dash: unmatched ')' in the plot specification.\n")
                        exit(198)
                    }
                    qdepth--
                }
                else if (qdepth == 0 & c_code == 124 & i + 1 <= len &
                         ascii(substr(trimmed, i + 1, 1)) == 124) {
                    graph_qual = graph_qual + " " +
                                 strtrim(substr(trimmed, qual_start, i - qual_start))
                    qual_seen = 0
                    i = i + 2
                    continue
                }
                else if (qdepth == 0 & c_code == 44) {
                    graph_qual = graph_qual + " " +
                                 strtrim(substr(trimmed, qual_start, i - qual_start))
                    qual_seen = 0
                    graph_opts_raw = strtrim(substr(trimmed, i + 1, .))
                    if (graph_opts_raw != "" &
                        ascii(substr(graph_opts_raw, 1, 1)) == 40) {
                        errprintf(
                          "dash: a plot group may not follow the graph-option comma.\n")
                        errprintf(
                          "      Write every plot before the comma: (plot1) (plot2), <options>\n")
                        exit(198)
                    }
                    break
                }
                i++
                continue
            }

            if (c_code == 40 & depth == 0) {
                seg_start = i + 1
                depth     = 1
            }
            else if (c_code == 40) depth++
            else if (c_code == 41 & depth > 0) {
                depth--
                if (depth == 0 & seg_start > 0) {
                    seg_text = strtrim(substr(trimmed, seg_start, i - seg_start))
                    if (seg_text != "") {
                        n_segs = n_segs + 1
                        segs   = segs, seg_text
                    }
                    seg_start = 0
                }
            }
            else if (c_code == 41) {
                // A ')' with nothing open.  This used to fall through to
                // i++ and be ignored, so `(a)) (b)' drew both plots where
                // twoway returns r(198).
                errprintf("dash: unmatched ')' in the plot specification.\n")
                exit(198)
            }
            else if (c_code == 44 & depth == 0) {
                // top-level comma after all () groups → graph opts
                graph_opts_raw = strtrim(substr(trimmed, i + 1, .))
                // A graph option always begins with its own name, so a '('
                // opening this text is a plot group written after the
                // comma.  twoway returns r(198) for `(a), (b)'; dash used
                // to swallow the second group into the option string.
                if (graph_opts_raw != "" &
                    ascii(substr(graph_opts_raw, 1, 1)) == 40) {
                    errprintf(
                      "dash: a plot group may not follow the graph-option comma.\n")
                    errprintf(
                      "      Write every plot before the comma: (plot1) (plot2), <options>\n")
                    exit(198)
                }
                break
            }
            else if (depth == 0 & c_code != 32 & c_code != 9) {
                // "||" is a legal separator BETWEEN parenthesised groups:
                // twoway accepts `(scatter y x) || (line y x)', measured
                // rc 0.  Treating it as stray text rejected a form dash
                // claims drop-in parity for.
                if (c_code == 124) {
                    i++
                    continue
                }

                // A top-level if/in qualifier may follow a plot group:
                //     (scatter y x) if foreign==1, title("T")
                // twoway accepts it after the last group and before a
                // `||', with a blank or, for `if', a parenthesis after the
                // word (measured rc 0: `(scatter mpg weight) if(foreign==1)'
                // draws the 22 foreign cars); the word is lower case, as
                // Stata's own -syntax- reads it (`IF foreign==1' is
                // r(198) in twoway).  It is read by the branch above, from
                // the word on.
                qword = substr(trimmed, i, 2)
                qnext = (i + 2 <= len ? ascii(substr(trimmed, i+2, 1)) : 32)
                if ((qword == "if" & (qnext == 32 | qnext == 9 | qnext == 40)) |
                    (qword == "in" & (qnext == 32 | qnext == 9))) {
                    qual_seen  = 1
                    qual_start = i
                    qdepth     = 0
                    i = i + 2
                    continue
                }

                // Text between top-level groups, which twoway rejects --
                // `(a) junk (b)' is r(198) there and used to be rc 0 here
                // with `junk' silently discarded.  Report the whole word,
                // not the one character the scan happened to stop on.
                stray = substr(trimmed, i, .)
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

        // Reaching the end mid-construct means the specification is
        // malformed.  Both conditions used to yield one silent segment.
        // (A `break' at the top-level comma leaves the graph options
        // unscanned by design -- Stata's -syntax- validates those.)
        //
        // The quote is tested FIRST because an unterminated quote also
        // leaves `depth' stuck: `title("oops || line y x' is a missing '"',
        // and reporting it as a paren problem sends the user hunting for
        // the wrong character.
        if (in_dq | in_cq) {
            errprintf("dash: unterminated quotation in the plot specification.\n")
            exit(198)
        }
        if (depth != 0 | (qual_seen & qdepth != 0)) {
            errprintf("dash: unbalanced parentheses in the plot specification.\n")
            exit(198)
        }
        // A qualifier that runs to the end of the command.
        if (qual_seen) {
            graph_qual = graph_qual + " " + strtrim(substr(trimmed, qual_start, .))
        }
    }
    // ================================================================
    // FLAT MODE (|| separators)
    // ================================================================
    else {
        depth     = 0
        in_dq     = 0
        in_cq     = 0
        seg_start = 1
        i         = 1

        while (i <= len) {
            // Quoted text is opaque at ANY depth.  These two branches used
            // to carry `& depth == 0', so a '(' inside a quoted option
            // value was counted as a real parenthesis, `depth' never
            // returned to 0, and every later "||" stopped separating --
            // the whole of the remaining command was folded into segment 1
            // and reported as unknown options.  Paren mode never had the
            // gate and has always been the correct reference.
            nxt = _dash_quote_step(trimmed, len, i, in_dq, in_cq)
            if (nxt) {
                i = nxt
                continue
            }

            c_code = ascii(substr(trimmed, i, 1))

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
            if (c_code == 41) {
                // A ')' with nothing open.  Flat mode used to fall through
                // to i++ and ignore it, so `scatter y x, title("ok"))' was
                // rc 0 here and r(198) in twoway -- measured.  An
                // unbalanced ')' never leaves `depth' non-zero, so the
                // end-of-scan check below cannot catch this one.
                errprintf("dash: unmatched ')' in the plot specification.\n")
                exit(198)
            }

            // Check for "||" at depth 0
            if (c_code == 124 & depth == 0 &
                i + 1 <= len & ascii(substr(trimmed, i+1, 1)) == 124) {
                seg_text = strtrim(substr(trimmed, seg_start, i - seg_start))
                if (seg_text != "") {
                    n_segs = n_segs + 1
                    segs   = segs, seg_text
                }
                seg_start = i + 2
                i         = i + 2
                continue
            }
            i++
        }

        // Reaching the end mid-construct means the specification is
        // malformed.  Both conditions used to yield one silent segment:
        //     scatter y x, legend(off || line y2 x      -- unclosed '('
        //     scatter y x, title("oops || line y2 x     -- unterminated '"'
        //
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

        // final (or only) segment
        seg_text = strtrim(substr(trimmed, seg_start, .))
        if (seg_text != "") {
            n_segs = n_segs + 1
            segs   = segs, seg_text
        }

        // In flat mode graph-level options are embedded in the last segment
        // (handled by the Stata syntax call); no separate graph_opts_raw.
        graph_opts_raw = ""
    }

    if (n_segs == 0) {
        errprintf("dash: no plot specifications found.\n")
        exit(198)
    }

    // Store results in caller's local-macro environment
    st_local("_n_segs", strofreal(n_segs))
    for (i = 1; i <= n_segs; i++) {
        st_local("_seg_" + strofreal(i), segs[i])
    }
    st_local("_graph_opts_raw", graph_opts_raw)
    // The qualifier written between or after the parenthesised groups,
    // every piece of it, "" in flat mode, where a qualifier belongs to the
    // plot it is written in (twoway draws `scatter y x || line y x if
    // foreign==1' as 74 points and a line through 22).
    st_local("_graph_qual_raw", strtrim(graph_qual))
}


// ============================================================
// 6. JSON VARIABLE EXTRACTOR  (used by _dash_prepare_spec and
//    _dash_render_immediate)
// ============================================================
//
// Scans a plot-spec JSON string and collects all "yvar", "xvar",
// "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var" values,
// and the option-named variables "mlabel", "colorvar" and "wexp" (the
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
// dash_json_<name> and dash_spec_<name>, and a KPI's marker dash_kpi_<name>
// and its fields dash_kpi_<name>__<field> (_dash_kpi_fields).  Only the
// ones Stata holds are returned; an empty field is no global at all.
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
    own = ("dash_json_" + nm, "dash_spec_" + nm, "dash_kpi_" + nm)
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

// _dash_fn_names(expr, cap) -- the names a function expression calls.
//
// Every name written directly before a `(' -- as Stata reads a function
// call, with no space between -- outside double and compound quotes, and
// not the tail of a number or of another name, each once, at most cap of
// them, space-separated.  dash.ado asks Stata whether each is a function
// (_dash_fn_refuse); twoway refuses an expression calling one Stata does
// not have, "error in expression", r(133).  Every name returned is a Stata
// name of at most 32 characters, so it may be put on a command line.
// Linear in the length of expr.
string scalar _dash_fn_names(string scalar expr, real scalar cap)
{
    string scalar out, nm, prev
    real scalar   i, j, n, k, in_dq, in_cq, nxt, c

    n     = strlen(expr)
    out   = " "
    k     = 0
    in_dq = 0
    in_cq = 0
    i     = 1
    while (i <= n & k < cap) {
        nxt = _dash_quote_step(expr, n, i, in_dq, in_cq)
        if (nxt) {
            i = nxt
            continue
        }
        c = ascii(substr(expr, i, 1))
        if ((c >= 65 & c <= 90) | (c >= 97 & c <= 122) | c == 95) {
            prev = (i > 1 ? substr(expr, i - 1, 1) : " ")
            j = i
            while (j <= n) {
                c = ascii(substr(expr, j, 1))
                if (!((c >= 65 & c <= 90) | (c >= 97 & c <= 122) |
                      (c >= 48 & c <= 57) | c == 95)) break
                j++
            }
            nm = substr(expr, i, j - i)
            if (j <= n & substr(expr, j, 1) == "(" & strlen(nm) <= 32 &
                !(prev == "." | (ascii(prev) >= 48 & ascii(prev) <= 57))) {
                if (!strpos(out, " " + nm + " ")) {
                    out = out + nm + " "
                    k++
                }
            }
            i = j
            continue
        }
        i++
    }
    return(strtrim(out))
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
void _dash_axis_pieces(string scalar s)
{
    string rowvector tags, txts
    string scalar    head, tail, run, ch
    real scalar      n, i, k, in_dq, in_cq, nxt, was_in, sstart, bstart

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
            last[k] = toks[i]
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
// text() (each copy added), "R" everything else (the last copy).
string scalar _dash_rep_cat(string scalar key)
{
    string scalar k

    k = _dash_rep_bare(key)
    if (anyof(("title", "subtitle", "note", "caption", "xtitle", "ytitle",
               "xtitle2", "ytitle2", "t1title", "t2title", "b1title",
               "b2title", "l1title", "l2title", "r1title", "r2title",
               "title2", "subtitle2", "ztitle"), k)) return("T")
    if (anyof(("xlabel", "ylabel", "xlabel2", "ylabel2", "xtick", "ytick",
               "xmtick", "ymtick", "xmlabel", "ymlabel", "zlabel"), k)) return("L")
    if (anyof(("legend", "graphregion", "plotregion"), k)) return("I")
    if (anyof(("xscale", "yscale", "xscale2", "yscale2", "zscale"), k)) return("S")
    if (k == "by") return("B")
    if (k == "xline" | k == "yline") return("X")
    if (k == "text") return("A")
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
               // GAPS2 X2: colorvarminmax, now declared, is refused a
               // second time as twoway refuses it.  colorlevels() is NOT
               // here: twoway takes it twice (measured 26sep2026).
               "colorvarminmax"), k)) return(1)
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
    t = t \ ("headlabel",    "headlabel",    "head",      "0", pcs,         "0", "")
    t = t \ ("mwidth",       "mwidth",       "mw",        "0", "histogram rbar", "0", "")
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

// _dash_route_axis2(opts) -- the option list with ytitle(..., axis(2)) and
// xtitle(..., axis(2)) rewritten as ytitle2(...)/xtitle2(...), and an
// axis(1) word dropped (WP-28 B3).  It runs before -syntax- and before
// _dash_rep_reduce, whose merge would otherwise fold ytitle("a")
// ytitle("b", axis(2)) into one ytitle.  Only a word whose own name is a
// prefix of ytitle or xtitle, three characters or more (yti .. ytitle;
// never yti2), is touched; every other word, and every body, is returned
// byte for byte, so a title holding "axis(2)", a quote, $ or a backtick
// is kept as typed.  No regex (regexm follows the caller's version).
string scalar _dash_route_axis2(string scalar opts)
{
    string rowvector toks, sub_w
    string scalar    out, tok, nm, body, sub, w, arg, rest
    real scalar      i, j, route, any

    toks = _dash_rep_toks(opts, 0)
    if (cols(toks) == 0) return(opts)
    out  = ""
    any  = 0
    for (i = 1; i <= cols(toks); i++) {
        tok = toks[i]
        nm  = strlower(_dash_rep_optname(tok))
        if (strlen(nm) >= 3 & strlen(nm) <= 6 & strpos(tok, "(") &
            (substr("ytitle", 1, strlen(nm)) == nm |
             substr("xtitle", 1, strlen(nm)) == nm)) {
            if (_dash_rep_split(_dash_rep_value(tok), body, sub)) {
                sub_w = _dash_rep_toks(sub, 1)
                rest  = ""
                route = 0
                for (j = 1; j <= cols(sub_w); j++) {
                    w   = strlower(strtrim(sub_w[j]))
                    arg = ""
                    if (strlen(w) > 6 & substr(w, 1, 5) == "axis(" &
                        substr(w, strlen(w), 1) == ")") {
                        arg = strtrim(substr(w, 6, strlen(w) - 6))
                    }
                    if (arg == "1" | arg == "2") {
                        route = strtoreal(arg)
                        continue
                    }
                    rest = rest + (rest == "" ? "" : " ") + sub_w[j]
                }
                if (route) {
                    any = 1
                    tok = substr(nm, 1, 1) + "title" +
                          (route == 2 ? "2" : "") + "(" + body +
                          (rest == "" ? "" : ", " + rest) + ")"
                }
            }
        }
        toks[i] = tok
    }
    // Nothing routed: the list exactly as typed, spacing and all (and no
    // join, which the 10,000-copy exhaustion case TP-14e times).
    if (!any) return(opts)
    for (i = 1; i <= cols(toks); i++) out = out + (i > 1 ? " " : "") + toks[i]
    return(out)
}

// _dash_rep_subkey(tok, cat) -- which sub-option a word sets, for keeping
// the last of each: its name in lower case, a noX taken as X (grid and
// nogrid, box and nobox are one setting), pos as position, cols and rows
// as one (twoway: legend(cols(1)) legend(rows(1)) draws rows(1)), on and
// off as one, and label(# ...) keyed by its number.
string scalar _dash_rep_subkey(string scalar tok, string scalar cat)
{
    string scalar nm, v
    real scalar   p

    p  = strpos(tok, "(")
    nm = strlower(strtrim(p ? substr(tok, 1, p - 1) : tok))
    if (strlen(nm) > 2 & substr(nm, 1, 2) == "no") nm = substr(nm, 3, .)
    if (nm == "pos") nm = "position"
    if (nm == "cols" | nm == "rows") nm = "cols|rows"
    if (nm == "on" | nm == "off") nm = "on|off"
    if (nm == "label" & cat == "I" & p) {
        v = strtrim(_dash_rep_value(tok))
        nm = nm + " " + (strpos(v, " ") ? substr(v, 1, strpos(v, " ") - 1) : v)
    }
    return(nm)
}

// _dash_rep_subs(s1, s2, cat, drop) -- two sub-option lists as one: every
// word of s1 then s2, keeping only the last word of each setting
// (_dash_rep_subkey), in the order the kept words stand, less the words
// listed in drop (suffix, prefix, add: merging instructions, spent here).
// On an axis scale ("S") every range() is one range(), the union of the
// ranges written, as twoway draws xscale(range(0 8000)) xscale(range(1000
// 6000)) over 0 to 8000.
string scalar _dash_rep_subs(string scalar s1, string scalar s2,
                             string scalar cat, string rowvector drop)
{
    string rowvector w, keys
    string scalar    out, k
    real scalar      i, j, keep, lo, hi, v, nr, rng, ok
    real rowvector   nums

    w = _dash_rep_toks(s1, 1), _dash_rep_toks(s2, 1)
    keys = J(1, cols(w), "")
    for (i = 1; i <= cols(w); i++) keys[i] = _dash_rep_subkey(w[i], cat)
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
    out = ""
    for (i = 1; i <= cols(w); i++) {
        if (anyof(drop, strlower(w[i]))) continue
        keep = 1
        for (j = i + 1; j <= cols(w); j++) {
            if (keys[j] == keys[i]) {
                keep = 0
                break
            }
        }
        if (!keep) continue
        if (cat == "S" & i == rng & nr > 1 & ok) {
            out = out + (out == "" ? "" : " ") + "range(" +
                  strtrim(strofreal(lo, "%21.0g")) + " " +
                  strtrim(strofreal(hi, "%21.0g")) + ")"
            continue
        }
        out = out + (out == "" ? "" : " ") + w[i]
    }
    return(out)
}

// _dash_rep_merge(key, v1, v2) -- the value twoway draws for option key
// written first with value v1 and then with v2 (_dash_rep_cat says how).
string scalar _dash_rep_merge(string scalar key, string scalar v1,
                              string scalar v2)
{
    string scalar    cat, b1, s1, b2, s2, body, sub
    string rowvector w2, drop
    real scalar      c1, c2, has2, suf, pre, add

    cat = _dash_rep_cat(key)
    if (cat == "R" | strtrim(v1) == "") return(v2)
    if (strtrim(v2) == "") return(v1)
    if (cat == "A") return(v1 + " " + v2)
    if (cat == "X") return(v1 + ", " + v2)
    if (cat == "I" | cat == "S") {
        return(_dash_rep_subs(v1, v2, cat, J(1, 0, "")))
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
    sub = _dash_rep_subs(s1, s2, cat, drop)
    return(body + (sub != "" ? ", " + sub : ""))
}

// _dash_rep_merge_locals(key, m1, m2, out) -- _dash_rep_merge on the
// caller's locals m1 and m2, read by value, into its local out.
void _dash_rep_merge_locals(string scalar key, string scalar m1,
                            string scalar m2, string scalar out)
{
    st_local(out, _dash_rep_merge(key, st_local(m1), st_local(m2)))
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
        lastpos[k] = i
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

// _dash_fn_space_call(expr) -- the first operand of a function expression
// written with blanks before a `(', as `sin (x)' or `2 (x)', outside
// double and compound quotes; "" when there is none.
//
// Stata never reads a name and a parenthesis apart as a call: `twoway
// function y = sin (x)' is "error in expression", r(111) -- sin is looked
// for as a variable and not found -- where sin(x) is drawn; and a name the
// data does have (mpg, or mp for it), x, _n, _N and _pi, or a number, a
// string or a closing parenthesis before the blanks, are r(198).  With
// tabs alone between a name and its `(' it is r(133), an unknown function
// (measured 24sep2026).  2 * (x) and x + (1) have an operator before the
// `(' and are drawn.  Returns "N <pos> <name>" for a name (not the tail of
// a number or of a dotted name) and blanks holding a space, "T <pos>
// <name>" for a name and tabs alone, "O <pos>" for any other operand, pos
// being where the operand begins, so the caller can ask which of this and
// an unknown function Stata meets first.  Linear in the length of expr.
string scalar _dash_fn_space_call(string scalar expr)
{
    string scalar ch
    real scalar   i, j, n, in_dq, in_cq, nxt, c, c0, lastkind, lastpos
    real scalar   lastend, blank, qstart

    n        = strlen(expr)
    in_dq    = 0
    in_cq    = 0
    lastkind = 0
    lastpos  = 0
    lastend  = 0
    blank    = 0
    qstart   = 0
    i        = 1
    while (i <= n) {
        if (!in_dq & !in_cq) qstart = i
        nxt = _dash_quote_step(expr, n, i, in_dq, in_cq)
        if (nxt) {
            // A closed string is an operand; it began where the quote
            // opened (qstart holds the position before it opened).
            if (!in_dq & !in_cq) {
                lastkind = 3
                blank    = 0
            }
            else if (lastkind != 4) {
                lastpos  = qstart
                lastkind = 4
            }
            i = nxt
            continue
        }
        ch = substr(expr, i, 1)
        c  = ascii(ch)
        if (ch == " ") {
            if (lastkind) blank = 1
            i++
            continue
        }
        if (ch == char(9)) {
            if (lastkind & !blank) blank = 2
            i++
            continue
        }
        if (ch == "(") {
            if (lastkind & blank) {
                if (lastkind == 1) {
                    return((blank == 1 ? "N " : "T ") + strofreal(lastpos) + " " +
                           substr(expr, lastpos, lastend - lastpos + 1))
                }
                return("O " + strofreal(lastpos))
            }
            lastkind = 0
            blank    = 0
            i++
            continue
        }
        if ((c >= 65 & c <= 90) | (c >= 97 & c <= 122) | c == 95 |
            (c >= 48 & c <= 57) | c == 46) {
            c0 = c
            j  = i
            while (j <= n) {
                c = ascii(substr(expr, j, 1))
                if (!((c >= 65 & c <= 90) | (c >= 97 & c <= 122) |
                      (c >= 48 & c <= 57) | c == 95 | c == 46)) break
                j++
            }
            // A name begins with a letter or _ and holds no dot; anything
            // else here (2, 1.5, 1e5, a.b) is some other operand.
            if (((c0 >= 65 & c0 <= 90) | (c0 >= 97 & c0 <= 122) | c0 == 95) &
                !strpos(substr(expr, i, j - i), ".")) lastkind = 1
            else lastkind = 3
            lastpos = i
            lastend = j - 1
            blank   = 0
            i = j
            continue
        }
        if (ch == ")") {
            lastkind = 3
            lastpos  = i
            blank    = 0
            i++
            continue
        }
        // An operator, a comma or anything else: no operand before a `('.
        lastkind = 0
        blank    = 0
        i++
    }
    return("")
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

end
