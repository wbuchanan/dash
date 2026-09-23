*! dash_parse.mata  v2.0
*! Mata utilities for the dash command.
*!
*! This version delegates ALL option parsing to Stata's syntax command.
*! Mata is responsible only for:
*!   1. Character-level helpers  (UTF-8 validation, JSON/HTML escaping)
*!   2. Plot-segment splitting   (|| flat syntax and () paren syntax)
*!   3. Option-key abbreviation expansion (pre-processing before syntax)
*!   4. JSON variable extraction (used by _dash_build / _dash_serve)
*!
*! Public API (called from dash.ado via mata: statements)
*!   _dash_check_utf8(s)
*!       Validate UTF-8.  Calls exit(198) on failure.
*!
*!   _dash_say(style, before, value, after)
*!       Print before + value + after as one line in SMCL style "err",
*!       "txt" or "res", every character shown as written (_dash_smcl_text).
*!
*!   _dash_is_digits(s, maxlen)
*!       1 when s is 1..maxlen ASCII digits and nothing else.
*!
*!   _dash_layout_cells(layout)
*!       Cells an explicit layout() grid asks for, or missing.
*!
*!   _dash_layout_refusal(layout, registry)
*!       "" when dash build can draw layout() as written, else the refusal.
*!
*!   _dash_split_segs(input)
*!       Split the raw command line into plot segments + graph-opts string.
*!       Sets in the *caller's* local-macro environment:
*!           _n_segs          : number of plot segments (string of integer)
*!           _seg_1 .. _seg_N : full text of each segment (incl. plot type)
*!           _graph_opts_raw  : graph-level option text (may be empty)
*!
*!   _dash_expand_plottype(abbrev, out_macro)
*!       Expand a plot-type abbreviation; store full name in out_macro.
*!       Stores "" if the abbreviation is unrecognised.
*!
*!   _dash_comma_pos(input, out_macro)
*!       Position (1-based) of the first top-level comma, or "0".
*!
*!
*!   _dash_extract_vars(json_str, out_macro)
*!       Extract variable-name tokens from a plot-spec JSON string.
*!       Used by _dash_build and _dash_serve to collect the jsonio varlist.
*!
*!   _dash_json_esc(s, out_macro)   — JSON-escape s, store in out_macro
*!   _dash_html_esc(s, out_macro)   — HTML-escape s, store in out_macro
*!
*!   _dash_json_get_str(json_str, key, out_macro)
*!       Extract a JSON string field value by key, correctly handling \"
*!       escape sequences inside the value.  Used by _dash_render_immediate.
*!
*! Version: 2.0  27mar2026

// ============================================================
// Compile into memory
// ============================================================
mata:

// ============================================================
// 1. CHARACTER-LEVEL HELPERS
// ============================================================

// JSON escaping: backslash, double-quote, and common control chars
string scalar _json_escape(string scalar s) {
    string scalar out
    real   scalar i, c
    out = ""
    for (i = 1; i <= strlen(s); i++) {
        c = ascii(substr(s, i, 1))
        if      (c == 92)  out = out + "\\\\"
        else if (c == 34)  out = out + "\\" + char(34)
        else if (c ==  8)  out = out + "\\b"
        else if (c ==  9)  out = out + "\\t"
        else if (c == 10)  out = out + "\\n"
        else if (c == 13)  out = out + "\\r"
        else               out = out + substr(s, i, 1)
    }
    return(out)
}

// HTML escaping for text embedded in HTML output
string scalar _html_escape(string scalar s) {
    string scalar out
    out = subinstr(s,  "&",  "&amp;",  .)
    out = subinstr(out, "<",  "&lt;",   .)
    out = subinstr(out, ">",  "&gt;",   .)
    out = subinstr(out, char(34), "&quot;", .)
    out = subinstr(out, "'",  "&#39;",  .)
    return(out)
}

// Stata-accessible wrappers
void _dash_json_esc(string scalar s, string scalar out_macro) {
    st_local(out_macro, _json_escape(s))
}
void _dash_html_esc(string scalar s, string scalar out_macro) {
    st_local(out_macro, _html_escape(s))
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
// registry, as link() and exclude() require, and every span a whole number
// from 1 to 12 written in at most two digits.  dash_render.py's
// _dash_layout_check() reports the same problems in a spec that did not
// come through dash.ado.
// ============================================================
string scalar _dash_layout_refusal(string scalar layout, string scalar registry) {
    string scalar    s, form, names, spec, tok, nm, span
    string rowvector reg, nms, toks
    real scalar      i, eq

    form = "layout() must be 'auto', 'N M' grid (N and M >= 1), " +
           "'name:row,col' placement, or 'bs[: name=span ...]' Bootstrap layout."
    s = layout
    for (i = 9; i <= 13; i++) s = subinstr(s, char(i), " ")
    s = strtrim(s)
    if (s == "" | s == "auto") return("")
    reg = tokens(registry)

    if (strlower(substr(s, 1, 2)) == "bs") {
        spec = strtrim(substr(s, 3, .))
        if (spec == "") return("")
        if (substr(spec, 1, 1) != ":") return(form)
        spec = strtrim(substr(spec, 2, .))
        if (spec == "") return(form)
        spec = subinstr(spec, "/", " ")
        toks = tokens(spec)
        for (i = 1; i <= cols(toks); i++) {
            tok = toks[i]
            eq  = strpos(tok, "=")
            nm  = (eq ? substr(tok, 1, eq - 1) : tok)
            if (!_dash_is_name(nm)) return(form)
            if (!anyof(reg, nm)) return("layout() name '" + nm + "' not found in registry.")
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
    }
    return("")
}



// ============================================================
// 2. PLOT-TYPE ABBREVIATION EXPANSION
// ============================================================

string scalar _expand_plottype_str(string scalar name) {
    string matrix tbl
    string scalar full, minab, hit
    real scalar   i, nhits

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
        ("scatteri","scatteri")

    nhits = 0
    hit   = ""
    for (i = 1; i <= rows(tbl); i++) {
        full  = tbl[i,1]
        minab = tbl[i,2]
        if (strlen(name) >= strlen(minab) &
            substr(full, 1, strlen(name)) == name) {
            nhits = nhits + 1
            hit   = full
        }
    }
    if (nhits == 1) return(hit)
    return("")   // unrecognised, or an ambiguous prefix
}

void _dash_expand_plottype(string scalar abbrev, string scalar out_macro) {
    st_local(out_macro, _expand_plottype_str(strlower(strtrim(abbrev))))
}


// ============================================================
// 3. OPTION-KEY ABBREVIATION EXPANSION
// ============================================================

// Expand a single option-key abbreviation to its full name.
// Returns the original key if no match (passes through unknown options).
// _expand_optkey was removed here.  dash used to declare every option in
// lowercase -- which tells Stata's syntax to permit NO abbreviation -- and then
// fake abbreviation with a fixed lookup table.  That table accepted exactly one
// short form per option, rejected every other prefix Stata accepts, and mapped
// eight abbreviations to the WRONG option: xl and yl went to xline/yline where
// Stata sends them to xlabel/ylabel, and m, mlc, mls, mlp and mlw were likewise
// mis-routed.  The syntax declarations in dash.ado now carry Stata's own
// measured minimum abbreviations, so Stata resolves prefixes itself and option
// words pass through this file untouched.


// Expand all option-key abbreviations in an options string.
// Input  example: "mc(red) ms(oh) title("My Graph")"
// Output example: "mcolor(red) msymbol(oh) title(My Graph)"
//
// Algorithm: scan character by character.
//   • At depth 0: accumulate a "word" buffer until we hit ( or whitespace/end.
//     When we hit '(' the accumulated word is an option key → expand it.
//     When we hit whitespace/end without '(' it is a bare flag option → expand it.
//   • At depth > 0 (inside parentheses): copy verbatim (it is an option value).
//   • Inside double-quoted strings: copy verbatim.
//   • Inside compound-quoted strings `"..."': copy verbatim.
//
// Note: Values inside parentheses are copied without modification so that
// variable names, expressions, and quoted strings are preserved exactly.
// _dash_expand_opts_str was removed here together with _expand_optkey.
// With option keys no longer rewritten, it was a verified identity function --
// it returned its input unchanged for nested parentheses, quoted values
// containing commas, repeated whitespace, bare flags and the empty string --
// so every call site now passes the raw option text straight to -syntax-.



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
//     `"..."'    compound quotes, which may themselves contain '"'
//
// Returns the index just past whatever it consumed, or 0 when the
// character at `i' is not quote-related and the caller should handle it
// itself.  `in_dq' and `in_cq' are updated in place -- Mata passes
// arguments by reference, verified by probe.
//
real scalar _dash_quote_step(string scalar s,
                             real scalar len,
                             real scalar i,
                             real scalar in_dq,
                             real scalar in_cq)
{
    real scalar c_code

    c_code = ascii(substr(s, i, 1))

    // Inside a compound quote: it ends on the two-character sequence "'
    // and a bare '"' within it is ordinary text.
    if (in_cq) {
        if (c_code == 34 & i + 1 <= len & ascii(substr(s, i+1, 1)) == 39) {
            in_cq = 0
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
    real   scalar  qual_seen, qnext
    string vector  segs
    string scalar  graph_opts_raw

    trimmed        = strtrim(input)
    len            = strlen(trimmed)
    n_segs         = 0
    segs           = J(1, 0, "")
    graph_opts_raw = ""

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
        i         = 1

        while (i <= len) {
            // Quoted text is opaque at any depth.
            nxt = _dash_quote_step(trimmed, len, i, in_dq, in_cq)
            if (nxt) {
                i = nxt
                continue
            }

            c_code = ascii(substr(trimmed, i, 1))

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

                // A top-level if/in qualifier may follow the plot groups:
                //     (scatter y x) if foreign==1, title("T")
                // twoway accepts all four shapes of this (measured rc 0)
                // and dash.sthlp documents them.  This scanner has always
                // walked past such a qualifier without capturing it,
                // leaving the top-level comma to be found as usual; that
                // is preserved exactly.  Policing stray text stops here so
                // the qualifier's own words are not mistaken for it.
                if (!qual_seen) {
                    qword = strlower(substr(trimmed, i, 2))
                    qnext = (i + 2 <= len ? ascii(substr(trimmed, i+2, 1)) : 32)
                    if ((qword == "if" | qword == "in") &
                        (qnext == 32 | qnext == 9)) {
                        qual_seen = 1
                        i = i + 2
                        continue
                    }
                }
                if (qual_seen) {
                    i++
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
        if (depth != 0) {
            errprintf("dash: unbalanced parentheses in the plot specification.\n")
            exit(198)
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
}


// ============================================================
// 6. JSON VARIABLE EXTRACTOR  (used by _dash_build / _dash_serve)
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
//   "by"      — each token in the varlist (before the first comma)
//   "if_expr" — identifier tokens extracted from the Python expression
//
// Only tokens that pass ^[a-zA-Z_][a-zA-Z0-9_]*$ and are not
// Python keywords/constants are returned.  Callers in dash.ado
// should use `capture confirm variable' to discard any tokens
// that are not real dataset variables (e.g. string literals that
// happened to look like identifiers in the expression).
//
// Appends discovered names (without duplicates) to the
// space-separated varlist stored in out_macro.
// ============================================================
void _dash_extract_qual_vars(string scalar json_str,
                              string scalar out_macro) {
    string rowvector by_keys, expr_keys, reserved, toks
    string scalar    varlist, val, tok, ch
    real scalar      pos, local_pos, orig_pos, n, k, t, comma_pos

    // Python expression keywords/constants that are not Stata variable names.
    reserved = ("True", "False", "None", "nan", "NaN", "inf",
                "and",  "or",    "not",  "in",  "is")

    by_keys   = (char(34) + "by"      + char(34) + ":")
    expr_keys = (char(34) + "if_expr" + char(34) + ":")

    varlist = ""
    n       = strlen(json_str)

    // ----------------------------------------------------------
    // Helper: decode the next JSON string value starting just
    // after the key's colon.  On entry pos points to the char
    // immediately following the key+colon (before optional
    // whitespace).  On return pos is set to one char past the
    // closing quote (or at n+1 if the string was unterminated).
    // The decoded value is returned in val.
    //
    // Escape sequences handled: \" → skip (no char added),
    // \\ → skip, all other \x → skip.  This strips inner quotes
    // from expressions like  make == \"AMC\"  so that "AMC"
    // does not yield false tokens; variable names remain intact.
    // ----------------------------------------------------------

    // ---- Extract "by" values ----
    for (k = 1; k <= cols(by_keys); k++) {
        pos = 1
        while (pos <= n) {
            orig_pos  = pos
            local_pos = strpos(substr(json_str, orig_pos, .), by_keys[k])
            if (local_pos == 0) break
            pos = orig_pos + local_pos - 1 + strlen(by_keys[k])
            // Skip optional whitespace before opening quote
            while (pos <= n &
                   (substr(json_str, pos, 1) == " " |
                    substr(json_str, pos, 1) == char(9))) pos++
            if (pos > n | substr(json_str, pos, 1) != char(34)) continue
            pos++   // skip opening quote
            val = ""
            while (pos <= n) {
                ch = substr(json_str, pos, 1)
                if (ch == char(34)) break           // unescaped closing quote
                if (ch == "\\" & pos + 1 <= n) {
                    pos = pos + 2; continue         // skip escape sequence
                }
                val = val + ch
                pos++
            }
            pos++   // skip closing quote
            // Only tokenize before the first comma to avoid option keywords
            // such as "cols", "total", "missing" in by(varlist, opts).
            comma_pos = strpos(val, ",")
            if (comma_pos > 0) val = substr(val, 1, comma_pos - 1)
            toks = tokens(val)
            for (t = 1; t <= cols(toks); t++) {
                tok = toks[t]
                if (regexm(tok, "^[a-zA-Z_][a-zA-Z0-9_]*$") &
                    !anyof(tokens(varlist), tok)) {
                    if (varlist != "") varlist = varlist + " "
                    varlist = varlist + tok
                }
            }
        }
    }

    // ---- Extract "if_expr" values ----
    for (k = 1; k <= cols(expr_keys); k++) {
        pos = 1
        while (pos <= n) {
            orig_pos  = pos
            local_pos = strpos(substr(json_str, orig_pos, .), expr_keys[k])
            if (local_pos == 0) break
            pos = orig_pos + local_pos - 1 + strlen(expr_keys[k])
            while (pos <= n &
                   (substr(json_str, pos, 1) == " " |
                    substr(json_str, pos, 1) == char(9))) pos++
            if (pos > n | substr(json_str, pos, 1) != char(34)) continue
            pos++   // skip opening quote
            val = ""
            while (pos <= n) {
                ch = substr(json_str, pos, 1)
                if (ch == char(34)) break
                if (ch == "\\" & pos + 1 <= n) {
                    pos = pos + 2; continue     // skip \" and other escapes
                }
                val = val + ch
                pos++
            }
            pos++   // skip closing quote
            // Replace operator and punctuation characters with spaces so
            // that tokens() returns only identifier-like strings.
            val = subinstr(val, "==", " ", .)
            val = subinstr(val, "!=", " ", .)
            val = subinstr(val, "~=", " ", .)
            val = subinstr(val, "<=", " ", .)
            val = subinstr(val, ">=", " ", .)
            val = subinstr(val, "<",  " ", .)
            val = subinstr(val, ">",  " ", .)
            val = subinstr(val, "&",  " ", .)
            val = subinstr(val, "|",  " ", .)
            val = subinstr(val, "!",  " ", .)
            val = subinstr(val, "(",  " ", .)
            val = subinstr(val, ")",  " ", .)
            val = subinstr(val, "+",  " ", .)
            val = subinstr(val, "-",  " ", .)
            val = subinstr(val, "*",  " ", .)
            val = subinstr(val, "/",  " ", .)
            val = subinstr(val, "%",  " ", .)
            val = subinstr(val, ",",  " ", .)
            val = subinstr(val, char(34), " ", .)
            toks = tokens(val)
            for (t = 1; t <= cols(toks); t++) {
                tok = toks[t]
                // Keep only Stata-identifier-like tokens; skip Python
                // reserved words and numeric literals.
                if (regexm(tok, "^[a-zA-Z_][a-zA-Z0-9_]*$") &
                    !anyof(reserved, tok) &
                    !anyof(tokens(varlist), tok)) {
                    if (varlist != "") varlist = varlist + " "
                    varlist = varlist + tok
                }
            }
        }
    }

    st_local(out_macro, strtrim(varlist))
}


// ============================================================
// 6.  FILTER EXTRACTION
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
// Called from _dash_build BEFORE syntax runs.
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
// 7.  JSON STRING VALUE EXTRACTOR
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
// Called from _dash_render_immediate in dash.ado.
// ============================================================
void _dash_json_get_str(string scalar json_str,
                        string scalar key,
                        string scalar out_macro) {
    string scalar needle, sub, ch, value
    real scalar   pos, local_pos, n

    // Build search pattern:  "key":"
    needle    = char(34) + key + char(34) + ":" + char(34)
    local_pos = strpos(json_str, needle)
    if (local_pos == 0) {
        st_local(out_macro, "")
        return
    }

    // Start reading value characters just after the opening "
    pos   = local_pos + strlen(needle)
    n     = strlen(json_str)
    value = ""

    while (pos <= n) {
        ch = substr(json_str, pos, 1)
        if (ch == char(34)) {
            // Unescaped closing double-quote — end of string value
            break
        }
        else if (ch == char(92)) {
            // Escape sequence — peek at next character.
            //
            // char(92), not "\\".  Mata does NOT collapse a doubled
            // backslash in a string literal the way C does: measured,
            // strlen("\\") is 2 and "\\" == char(92) is false.  So every
            // one of these comparisons was a 1-character string against a
            // 2-character one, never true, and this decoder has never
            // decoded anything.  The first backslash of an escape fell
            // through to the plain-character branch and the '"' that
            // followed it was read as the closing quote, so
            //     "if_expr": "make == \"AMC Concord\""
            // -- the very case this function was written for -- came back
            // as a single backslash.
            if (pos + 1 <= n) {
                ch = substr(json_str, pos + 1, 1)
                if      (ch == char(34)) value = value + char(34)
                else if (ch == char(92)) value = value + char(92)
                else if (ch == "n")      value = value + char(10)
                else if (ch == "r")      value = value + char(13)
                else if (ch == "t")      value = value + char(9)
                else                     value = value + char(92) + ch
                pos = pos + 2
            }
            else {
                // Trailing backslash with no next char — keep it
                value = value + char(92)
                pos++
            }
        }
        else {
            value = value + ch
            pos++
        }
    }

    st_local(out_macro, value)
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
// ============================================================
// _dash_item_globals — every global belonging to one registry item
// ============================================================
//
// Graphs and KPIs share one registry and one namespace, and replacing an
// item of one kind with the other has to take the loser's globals with it --
// a name left carrying both a `dash_json_' and a `dash_kpi_' is skipped at
// build time, so the graph the user just registered would vanish.
//
// The match has to be EXACT rather than a prefix sweep.  `macro drop
// dash_kpi_g1*' also matches dash_kpi_g10 and every one of its suffixes, and
// the name grammar -- [a-zA-Z_][a-zA-Z0-9_]{0,31} -- lets g1 and g10 be
// registered at the same time.  Enumerating the suffixes instead would go
// stale the moment one is added, which is the failure `_dash_clear' records
// in its own comment.  Asking Stata what it actually holds has neither
// problem.
//
// Returns the matching global names, space separated, in out_macro.
//
void _dash_item_globals(string scalar nm, string scalar out_macro)
{
    string colvector all
    string scalar    hit, kpi_prefix
    real scalar      i

    hit        = ""
    kpi_prefix = "dash_kpi_" + nm + "_"
    all        = st_dir("global", "macro", "dash_*")

    for (i = 1; i <= length(all); i++) {
        if (all[i] == "dash_json_" + nm |
            all[i] == "dash_spec_" + nm |
            all[i] == "dash_kpi_"  + nm |
            substr(all[i], 1, strlen(kpi_prefix)) == kpi_prefix) {
            hit = hit + " " + all[i]
        }
    }
    st_local(out_macro, strtrim(hit))
}


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

end
