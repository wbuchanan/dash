*! dash_parse.mata
*! Two-pass Mata parser for dash command syntax.
*!
*! Pass 1 — Tokenizer: character-by-character scan producing a typed token array.
*! Pass 2 — Structural parser: groups tokens into plot specs and graph-level options,
*!           expands Stata abbreviations, validates plot types and variable names,
*!           and serialises the result to a JSON string stored in a Stata local macro.
*!
*! Public API
*!   dash_parse(input, result_macro)
*!     input        : raw command-line string (after the "dash" keyword and before eol)
*!     result_macro : name of the local macro that will receive the JSON string
*!
*! Error codes used
*!   198  invalid syntax / unsupported plot type / injection risk
*!   111  variable not found in dataset
*!
*! Author:  (see dash.sthlp)
*! Version: 1.0.0  25mar2026

// ============================================================
// Ensure the mata library block is compiled into memory
// ============================================================
mata:

// ------------------------------------------------------------
// Token type constants  (P1A-01)
// ------------------------------------------------------------
real scalar OPEN_PAREN()   return(1)
real scalar CLOSE_PAREN()  return(2)
real scalar WORD()         return(3)
real scalar COMMA()        return(4)
real scalar PIPE_PIPE()    return(5)
real scalar QUOTED_STRING() return(6)

// ------------------------------------------------------------
// Internal helper: escape a string for JSON embedding.
// Handles backslash, double-quote, and the four C0 controls
// most likely to appear in Stata option values.
// ------------------------------------------------------------
string scalar _json_escape(string scalar s) {
    string scalar out
    real   scalar i, c
    out = ""
    for (i = 1; i <= strlen(s); i++) {
        c = ascii(substr(s, i, 1))
        if      (c == 92)  out = out + "\\\\"   // backslash
        else if (c == 34)  out = out + "\\" + char(34)   // double-quote
        else if (c ==  8)  out = out + "\\b"
        else if (c ==  9)  out = out + "\\t"
        else if (c == 10)  out = out + "\\n"
        else if (c == 13)  out = out + "\\r"
        else               out = out + substr(s, i, 1)
    }
    return(out)
}

// ------------------------------------------------------------
// Internal helper: HTML-escape a string (for titles, labels
// that will be embedded verbatim in Bokeh HTML output).
// (P1A-43 / security requirement)
// ------------------------------------------------------------
string scalar _html_escape(string scalar s) {
    string scalar out
    out = subinstr(s, "&",  "&amp;",  .)
    out = subinstr(out, "<",  "&lt;",   .)
    out = subinstr(out, ">",  "&gt;",   .)
    out = subinstr(out, `"""', "&quot;", .)
    out = subinstr(out, "'",  "&#39;",  .)
    return(out)
}

// ------------------------------------------------------------
// Internal helper: validate that every byte is a legal UTF-8
// sequence.  Returns 1 if valid, 0 if not.  (P1A-16)
//
// Strategy: walk the string checking leading-byte patterns
// and confirming the expected number of continuation bytes.
// Non-UTF-8 bytes cause immediate rejection.
// ------------------------------------------------------------
real scalar _is_utf8(string scalar s) {
    real scalar i, len, b, expect
    len = strlen(s)
    i   = 1
    while (i <= len) {
        b = ascii(substr(s, i, 1))
        if      (b < 128)              expect = 0   // single-byte ASCII
        else if (b >= 194 & b <= 223)  expect = 1   // 2-byte
        else if (b >= 224 & b <= 239)  expect = 2   // 3-byte
        else if (b >= 240 & b <= 244)  expect = 3   // 4-byte
        else                           return(0)    // invalid leading byte
        // check continuation bytes
        real scalar j
        for (j = 1; j <= expect; j++) {
            if (i + j > len) return(0)
            b = ascii(substr(s, i + j, 1))
            if (b < 128 | b > 191) return(0)
        }
        i = i + expect + 1
    }
    return(1)
}

// ============================================================
// PASS 1 — TOKENIZER  (P1A-02 through P1A-06)
// ============================================================
// Returns a (N x 2) string matrix:
//   col 1 = token type (as string representation of integer)
//   col 2 = token text
//
// Also handles:
//   - double-quoted strings "..."        (P1A-03)
//   - compound-quoted strings `"..."'    (P1A-04)
//   - || separator                       (P1A-05)
//   - comma at depth 0 vs inside parens  (P1A-06)
// ------------------------------------------------------------
string matrix _tokenize(string scalar input) {
    real   scalar  i, len, depth, c_code
    string scalar  ch, buf, tok_type
    string matrix  tokens
    real   scalar  inside_dq, inside_cq   // double-quote / compound-quote flags

    tokens     = J(0, 2, "")
    len        = strlen(input)
    depth      = 0
    inside_dq  = 0
    inside_cq  = 0
    buf        = ""
    i          = 1

    while (i <= len) {
        ch     = substr(input, i, 1)
        c_code = ascii(ch)

        // ---- double-quoted string begins: " ----
        if (inside_dq == 0 & inside_cq == 0 & ch == `"""') {
            // flush any accumulated word buffer
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            // consume until closing "
            inside_dq = 1
            buf = ""
            i = i + 1
            while (i <= len & substr(input, i, 1) != `"""') {
                buf = buf + substr(input, i, 1)
                i = i + 1
            }
            // i now points at closing " (or past end on malformed input)
            tokens = tokens \ (strofreal(QUOTED_STRING()), buf)
            buf = ""
            inside_dq = 0
            i = i + 1  // skip closing "
            continue
        }

        // ---- compound-quoted string begins: `" ----
        if (inside_dq == 0 & inside_cq == 0 & ch == "`") {
            if (i + 1 <= len & substr(input, i+1, 1) == `"""') {
                // flush word buffer
                if (buf != "") {
                    tokens = tokens \ (strofreal(WORD()), buf)
                    buf = ""
                }
                i = i + 2  // skip `"
                inside_cq = 1
                buf = ""
                // consume until closing "'
                while (i <= len) {
                    if (substr(input, i, 1) == `"""' & i+1 <= len & substr(input, i+1, 1) == "'") {
                        // closing "'  found
                        i = i + 2
                        break
                    }
                    buf = buf + substr(input, i, 1)
                    i = i + 1
                }
                tokens = tokens \ (strofreal(QUOTED_STRING()), buf)
                buf = ""
                inside_cq = 0
                continue
            }
        }

        // ---- not inside any quoted string ----

        // open paren
        if (ch == "(") {
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            depth = depth + 1
            tokens = tokens \ (strofreal(OPEN_PAREN()), "(")
            i = i + 1
            continue
        }

        // close paren
        if (ch == ")") {
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            if (depth > 0) depth = depth - 1
            tokens = tokens \ (strofreal(CLOSE_PAREN()), ")")
            i = i + 1
            continue
        }

        // pipe-pipe: ||  (P1A-05)
        if (ch == "|" & i+1 <= len & substr(input, i+1, 1) == "|") {
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            tokens = tokens \ (strofreal(PIPE_PIPE()), "||")
            i = i + 2
            continue
        }

        // comma  (P1A-06)
        if (ch == ",") {
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            tokens = tokens \ (strofreal(COMMA()), ",")
            i = i + 1
            continue
        }

        // whitespace — ends current word
        if (c_code == 32 | c_code == 9 | c_code == 10 | c_code == 13) {
            if (buf != "") {
                tokens = tokens \ (strofreal(WORD()), buf)
                buf = ""
            }
            i = i + 1
            continue
        }

        // regular character — accumulate into word buffer
        buf = buf + ch
        i = i + 1
    }

    // flush trailing buffer
    if (buf != "") {
        tokens = tokens \ (strofreal(WORD()), buf)
    }

    return(tokens)
}


// ============================================================
// ABBREVIATION EXPANSION ENGINE  (P1A-10, P1A-11, P1A-12, P1A-13)
// ============================================================
// Returns expanded option name, or the original if no match.
// ------------------------------------------------------------
string scalar _expand_abbrev(string scalar name) {
    // ---- plot-type abbreviations ----
    if (name == "sc")          return("scatter")
    if (name == "li")          return("line")
    if (name == "con")         return("connected")
    if (name == "ar")          return("area")
    if (name == "ba")          return("bar")
    if (name == "sp")          return("spike")
    if (name == "lfi")         return("lfit")
    if (name == "qfi")         return("qfit")
    if (name == "lfitci")      return("lfitci")    // no short form needed, exact
    if (name == "qfitci")      return("qfitci")
    if (name == "low")         return("lowess")
    if (name == "lpo")         return("lpoly")
    if (name == "lpol")        return("lpoly")
    if (name == "lpolyci")     return("lpolyci")    // exact match, keep
    if (name == "fp")          return("fpfit")
    if (name == "fpf")         return("fpfit")
    if (name == "fpfitci")     return("fpfitci")    // exact match, keep
    if (name == "hist")        return("histogram")
    if (name == "kde")         return("kdensity")
    if (name == "rarea")       return("rarea")
    if (name == "rbar")        return("rbar")
    if (name == "rspike")      return("rspike")
    if (name == "rcap")        return("rcap")
    if (name == "rline")       return("rline")
    if (name == "rconnected")  return("rconnected")
    if (name == "dot")         return("dot")
    if (name == "dr")          return("dropline")
    if (name == "rcapsym")     return("rcapsym")
    if (name == "pcspike")     return("pcspike")
    if (name == "pcarrow")     return("pcarrow")
    if (name == "pcbarrow")    return("pcbarrow")
    if (name == "tsl")         return("tsline")
    if (name == "tsrl")        return("tsrline")
    if (name == "msp")         return("mspline")
    if (name == "func")        return("function")

    // ---- marker options  (P1A-10) ----
    if (name == "mc")    return("mcolor")
    if (name == "ms")    return("msymbol")
    if (name == "msi")   return("msize")
    if (name == "mla")   return("mlabel")
    if (name == "mlc")   return("mlabcolor")
    if (name == "mls")   return("mlabsize")
    if (name == "mlp")   return("mlabposition")
    if (name == "mlg")   return("mlabgap")
    if (name == "mlw")   return("mlabwidth")
    if (name == "m")     return("marker")

    // ---- fill options ----
    if (name == "fc")    return("fcolor")
    if (name == "fi")    return("fintensity")

    // ---- marker fill / bar color options ----
    if (name == "mfc")   return("mfcolor")
    if (name == "blc")   return("blcolor")
    if (name == "bfc")   return("bfcolor")
    if (name == "bw")    return("barwidth")

    // ---- line options  (P1A-11) ----
    if (name == "lc")    return("lcolor")
    if (name == "lw")    return("lwidth")
    if (name == "lp")    return("lpattern")

    // ---- graph-level options  (P1A-12) ----
    if (name == "ti")    return("title")
    if (name == "sub")   return("subtitle")
    if (name == "xti")   return("xtitle")
    if (name == "yti")   return("ytitle")
    if (name == "xla")   return("xlabel")
    if (name == "yla")   return("ylabel")
    if (name == "note")  return("note")
    if (name == "cap")   return("caption")
    if (name == "leg")   return("legend")
    if (name == "sav")   return("saving")
    if (name == "nam")   return("name")
    if (name == "by")    return("by")
    if (name == "xsc")   return("xscale")
    if (name == "ysc")   return("yscale")
    if (name == "xl")    return("xline")
    if (name == "yl")    return("yline")
    if (name == "asp")   return("aspectratio")
    if (name == "bgc")   return("bgcolor")
    if (name == "pbgc")  return("plotbgcolor")
    if (name == "plotr") return("plotregion")
    if (name == "graphr") return("graphregion")

    // jitter options (plot-level)
    if (name == "jit")   return("jitter")
    if (name == "jse")   return("jseed")

    // dual-axis options (plot-level)
    if (name == "yax")   return("yaxis")
    if (name == "xax")   return("xaxis")

    // secondary-axis graph-level options
    if (name == "yti2")  return("ytitle2")
    if (name == "xti2")  return("xtitle2")
    if (name == "yla2")  return("ylabel2")
    if (name == "xla2")  return("xlabel2")
    if (name == "ysc2")  return("yscale2")
    if (name == "xsc2")  return("xscale2")

    // scheme option (build-level, but also parsed at graph level for pass-through)
    if (name == "sch")   return("scheme")

    // alpha / transparency options
    if (name == "mal")   return("malpha")
    if (name == "lal")   return("lalpha")
    if (name == "fal")   return("falpha")

    // variable color mapping
    if (name == "cv")    return("colorvar")
    if (name == "colv")  return("colorvar")
    if (name == "colpal")  return("colpalette")

    // no match — return original (handles full names and unknown abbrevs)
    return(name)
}


// ============================================================
// Supported plot types list  (P1A-14)
// ============================================================
real scalar _is_supported_plot(string scalar ptype) {
    string rowvector supported
    supported = ("scatter", "line", "connected", "area", "bar", "spike",
                 "lfit", "qfit", "lfitci", "qfitci", "lowess",
                 "lpoly", "lpolyci", "fpfit", "fpfitci",
                 "histogram", "kdensity",
                 "rarea", "rbar", "rspike", "rcap", "rline", "rconnected",
                 "dot", "dropline", "rcapsym", "scatteri",
                 "pcspike", "pcarrow", "pcbarrow", "pci", "pcscatter",
                 "tsline", "tsrline",
                 "mspline", "mband",
                 "rscatter",
                 "function")
    return(anyof(supported, ptype))
}


// ============================================================
// Option value parser
// Parses a sequence of tokens that represent option key-value
// pairs of the form:  key(value) or key(val1 val2 ...) or
// bare key (flag options).
//
// Returns a string matrix (M x 2): col1=key, col2=value
// ============================================================
string matrix _parse_options(string matrix tokens, real scalar start, real scalar end_row) {
    string matrix opts
    string scalar key, val, tok_type, tok_text
    real   scalar i, depth, j

    opts = J(0, 2, "")
    i    = start

    while (i <= end_row) {
        tok_type = tokens[i, 1]
        tok_text = tokens[i, 2]

        // skip commas
        if (tok_type == strofreal(COMMA())) {
            i = i + 1
            continue
        }

        // a WORD or QUOTED_STRING at this level is an option key
        if (tok_type == strofreal(WORD()) | tok_type == strofreal(QUOTED_STRING())) {
            key = _expand_abbrev(strlower(tok_text))
            i   = i + 1

            // check if followed by OPEN_PAREN (key-value option)
            // Use nested if to avoid non-short-circuit & with array access
            if (i <= end_row) {
                if (tokens[i, 1] == strofreal(OPEN_PAREN())) {
                    i = i + 1  // skip (
                    val   = ""
                    depth = 1
                    j     = i
                    // collect until matching close paren
                    while (j <= end_row) {
                        if (depth <= 0) break
                        if (tokens[j, 1] == strofreal(OPEN_PAREN())) {
                            depth = depth + 1
                            val   = val + tokens[j, 2]
                        }
                        else if (tokens[j, 1] == strofreal(CLOSE_PAREN())) {
                            depth = depth - 1
                            if (depth > 0) val = val + tokens[j, 2]
                        }
                        else if (tokens[j, 1] == strofreal(QUOTED_STRING())) {
                            // quoted string value — preserve as-is
                            val = val + tokens[j, 2]
                        }
                        else {
                            if (val != "") val = val + " "
                            val = val + tokens[j, 2]
                        }
                        j = j + 1
                    }
                    i = j  // j is one past the closing )
                    // strip leading/trailing whitespace
                    val = strtrim(val)
                }
                else {
                    // bare flag option — no value
                    val = "1"
                }
            }
            else {
                // key at end of token stream — treat as bare flag
                val = "1"
            }

            opts = opts \ (key, _html_escape(val))
        }
        else {
            // skip non-key tokens
            i = i + 1
        }
    }

    return(opts)
}


// ============================================================
// PASS 2 — STRUCTURAL PARSER  (P1A-07 through P1A-09)
// ============================================================
// Builds a JSON array of graph specs from the token stream.
//
// Grammar (simplified):
//   input  = [if_clause] [in_clause] plot_specs [, graph_opts]
//   plot_specs = "(" plot_spec ")" {"(" plot_spec ")"} |
//                plot_spec {|| plot_spec}
//   plot_spec  = plot_type varlist [, plot_opts]
//
// Returns the JSON string.
// ============================================================
string scalar _parse_structure(string matrix tokens,
                                string scalar if_expr,
                                string scalar in_expr) {
    real   scalar  ntok, i, j, depth
    real   scalar  spec_start, spec_end
    string scalar  ptype, yvar, xvar, json_out
    string matrix  plot_specs_idx   // (K x 2): start row, end row of each spec
    string matrix  graph_opts_tokens
    string matrix  cur_plot_opts
    string scalar  tok_type
    real   scalar  in_paren_mode    // 1 = using ()-syntax, 0 = ||-syntax
    real   scalar  top_comma_pos    // position of first top-level comma after all specs
    string matrix  plots_json
    string scalar  graph_opts_str
    string matrix  gopts
    real   scalar  g, m
    string scalar  varlist_str
    string rowvector  varlist_words

    ntok = rows(tokens)
    if (ntok == 0) {
        errprintf("dash: empty plot specification.\n")
        exit(198)
    }

    // ---- detect syntax style ----
    // If the first non-whitespace token is OPEN_PAREN → parenthetical syntax
    // Otherwise → flat / ||-syntax
    in_paren_mode = 0
    for (i = 1; i <= ntok; i++) {
        if (tokens[i, 1] == strofreal(OPEN_PAREN())) {
            in_paren_mode = 1
            break
        }
        if (tokens[i, 1] == strofreal(WORD())) {
            break  // first meaningful token is a word → flat mode
        }
    }

    // ---- find the top-level comma separating plot specs from graph opts ----
    // (only commas at depth == 0 outside all parens)
    top_comma_pos = 0
    depth = 0
    for (i = 1; i <= ntok; i++) {
        if (tokens[i, 1] == strofreal(OPEN_PAREN()))  depth = depth + 1
        else if (tokens[i, 1] == strofreal(CLOSE_PAREN())) {
            if (depth > 0) depth = depth - 1
        }
        else if (tokens[i, 1] == strofreal(COMMA()) & depth == 0) {
            // The LAST top-level comma is the graph-options separator.
            // However we need the *last* such comma after all specs.
            top_comma_pos = i
            // Don't break — keep scanning to find the last one.
        }
    }

    // Determine boundary of the plot-spec region and graph-opts region
    real scalar spec_region_end
    spec_region_end = ntok
    if (top_comma_pos > 0) spec_region_end = top_comma_pos - 1

    // ---- collect graph-level option tokens ----
    if (top_comma_pos > 0 & top_comma_pos < ntok) {
        graph_opts_tokens = tokens[(top_comma_pos+1)::ntok, .]
    }
    else {
        graph_opts_tokens = J(0, 2, "")
    }

    // ---- extract individual plot spec boundaries ----
    plot_specs_idx = J(0, 2, "")

    if (in_paren_mode) {
        // Collect each top-level parenthesised group
        i = 1
        depth = 0
        while (i <= spec_region_end) {
            if (tokens[i, 1] == strofreal(OPEN_PAREN()) & depth == 0) {
                spec_start = i + 1
                depth = 1
                i = i + 1
                while (i <= spec_region_end & depth > 0) {
                    if (tokens[i, 1] == strofreal(OPEN_PAREN())) depth = depth + 1
                    else if (tokens[i, 1] == strofreal(CLOSE_PAREN())) depth = depth - 1
                    if (depth > 0) i = i + 1
                    else break
                }
                spec_end = i - 1
                plot_specs_idx = plot_specs_idx \ (strofreal(spec_start), strofreal(spec_end))
                i = i + 1  // skip close paren
            }
            else {
                i = i + 1
            }
        }
    }
    else {
        // Flat / ||-separated syntax
        // split on PIPE_PIPE tokens at depth 0
        spec_start = 1
        depth      = 0
        for (i = 1; i <= spec_region_end; i++) {
            if (tokens[i, 1] == strofreal(OPEN_PAREN()))  depth = depth + 1
            else if (tokens[i, 1] == strofreal(CLOSE_PAREN()) & depth > 0) depth = depth - 1
            else if (tokens[i, 1] == strofreal(PIPE_PIPE()) & depth == 0) {
                plot_specs_idx = plot_specs_idx \ (strofreal(spec_start), strofreal(i-1))
                spec_start = i + 1
            }
        }
        // last (or only) spec
        plot_specs_idx = plot_specs_idx \ (strofreal(spec_start), strofreal(spec_region_end))
    }

    // ---- parse each plot spec ----
    plots_json = J(0, 1, "")

    real scalar nspecs
    nspecs = rows(plot_specs_idx)
    if (nspecs == 0) {
        errprintf("dash: no plot specifications found.\n")
        exit(198)
    }

    for (g = 1; g <= nspecs; g++) {
        real scalar s_start, s_end, comma_in_spec
        string scalar plot_json, vopts_json
        string matrix popts

        s_start = strtoreal(plot_specs_idx[g, 1])
        s_end   = strtoreal(plot_specs_idx[g, 2])

        // skip if empty range
        if (s_start > s_end) continue

        // find the comma separating varlist from plot options (inside this spec)
        comma_in_spec = 0
        depth = 0
        for (i = s_start; i <= s_end; i++) {
            if (tokens[i, 1] == strofreal(OPEN_PAREN()))  depth = depth + 1
            else if (tokens[i, 1] == strofreal(CLOSE_PAREN()) & depth > 0) depth = depth - 1
            else if (tokens[i, 1] == strofreal(COMMA()) & depth == 0) {
                comma_in_spec = i
                break
            }
        }

        real scalar varlist_end
        varlist_end = (comma_in_spec > 0) ? comma_in_spec - 1 : s_end

        // extract plot type (first WORD token in spec)
        ptype = ""
        real scalar varlist_start
        varlist_start = s_start
        for (i = s_start; i <= varlist_end; i++) {
            if (tokens[i, 1] == strofreal(WORD())) {
                ptype = _expand_abbrev(strlower(tokens[i, 2]))
                varlist_start = i + 1
                break
            }
        }

        if (ptype == "") {
            errprintf("dash: could not identify plot type in spec %g.\n", g)
            exit(198)
        }

        // validate plot type  (P1A-14)
        if (!_is_supported_plot(ptype)) {
            errprintf("dash: unsupported plot type '%s'. ", ptype)
            errprintf("Supported types: scatter line connected area bar spike lfit qfit lfitci qfitci lowess lpoly lpolyci fpfit fpfitci histogram kdensity rarea rbar rspike rcap rline rconnected dot dropline rcapsym scatteri pcspike pcarrow pcbarrow pci pcscatter tsline tsrline mspline mband rscatter function\n")
            exit(198)
        }

        // extract variable list words  (P1A-08)
        // function: collect ALL tokens as expression string; other types: WORD tokens only
        varlist_words = J(1, 0, "")
        if (ptype == "function") {
            string scalar expr_raw
            expr_raw = ""
            for (i = varlist_start; i <= varlist_end; i++) {
                expr_raw = expr_raw + tokens[i, 2]
            }
            expr_raw = strtrim(expr_raw)
            // Remove optional "y=" prefix (twoway function y=sin(x) style)
            if (regexm(expr_raw, "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=")) {
                expr_raw = strtrim(regexr(expr_raw, "^[a-zA-Z][a-zA-Z0-9_]*[ ]*=", ""))
            }
            varlist_words = J(1, 1, expr_raw)
        }
        else {
            for (i = varlist_start; i <= varlist_end; i++) {
                if (tokens[i, 1] == strofreal(WORD())) {
                    varlist_words = varlist_words, tokens[i, 2]
                }
            }
        }

        // variable name validation  (P1A-15)
        // function type: validate expression characters only (not variable names)
        if (ptype == "function") {
            // Expression already extracted into varlist_words[1]
            if (cols(varlist_words) >= 1) {
                // Reject shell injection characters and null bytes
                if (regexm(varlist_words[1], "[;`\$\\\\]") | strpos(varlist_words[1], char(0)) > 0) {
                    errprintf("dash: unsafe characters in function expression.\n")
                    exit(198)
                }
            }
        }
        // scatteri takes literal numeric pairs, not variable names — validate as numbers
        else if (ptype == "scatteri") {
            for (i = 1; i <= cols(varlist_words); i++) {
                string scalar snum
                snum = varlist_words[i]
                if (!regexm(snum, "^-?[0-9]*\\.?[0-9]+$")) {
                    errprintf("dash: scatteri argument '%s' is not a valid number.\n", snum)
                    exit(198)
                }
            }
            if (mod(cols(varlist_words), 2) != 0) {
                errprintf("dash: scatteri requires an even number of arguments (y x pairs).\n")
                exit(198)
            }
        }
        else {
            // We call back into Stata using stata() which returns the rc
            for (i = 1; i <= cols(varlist_words); i++) {
                string scalar vname_check
                vname_check = varlist_words[i]
                // Reject obvious injection patterns in variable names
                if (regexm(vname_check, "[;`'\$]")) {
                    errprintf("dash: invalid character in variable name '%s'.\n", vname_check)
                    exit(198)
                }
                stata("confirm variable " + vname_check)
                // stata() exits with error automatically if variable not found
            }
        }

        // build variable assignment based on plot type
        // Most types: yvar xvar; histogram/kdensity: var only; range types: yvar1 yvar2 xvar
        // PC types: y1var x1var y2var x2var; function: expr; scatteri: values
        string scalar yvar1, yvar2, y1var, x1var, y2var, x2var, expr_val
        yvar   = ""
        xvar   = ""
        yvar1  = ""
        yvar2  = ""
        y1var  = ""
        x1var  = ""
        y2var  = ""
        x2var  = ""
        expr_val = ""

        if (anyof(("histogram", "kdensity"), ptype)) {
            // univariate: just one variable
            if (cols(varlist_words) >= 1) yvar = varlist_words[1]
        }
        else if (anyof(("rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym",
                        "tsrline"), ptype)) {
            // range plots: yvar1 yvar2 [xvar]
            if (cols(varlist_words) >= 1) yvar1 = varlist_words[1]
            if (cols(varlist_words) >= 2) yvar2 = varlist_words[2]
            if (cols(varlist_words) >= 3) xvar  = varlist_words[3]
        }
        else if (anyof(("pcspike", "pcarrow", "pcbarrow"), ptype)) {
            // paired-coordinate: y1var x1var y2var x2var
            if (cols(varlist_words) >= 1) y1var = varlist_words[1]
            if (cols(varlist_words) >= 2) x1var = varlist_words[2]
            if (cols(varlist_words) >= 3) y2var = varlist_words[3]
            if (cols(varlist_words) >= 4) x2var = varlist_words[4]
        }
        else if (ptype == "scatteri") {
            // literal numeric pairs — no variable names; values stored separately
            // varlist_words already validated as numeric pairs above
        }
        else if (ptype == "function") {
            // expression string stored in varlist_words[1]
            if (cols(varlist_words) >= 1) expr_val = varlist_words[1]
        }
        else {
            // standard: yvar xvar (includes dropline, tsline, mspline, line, scatter, etc.)
            if (cols(varlist_words) >= 1) yvar = varlist_words[1]
            if (cols(varlist_words) >= 2) xvar = varlist_words[2]
        }

        // parse plot-level options
        if (comma_in_spec > 0 & comma_in_spec < s_end) {
            popts = _parse_options(tokens, comma_in_spec + 1, s_end)
        }
        else {
            popts = J(0, 2, "")
        }

        // build plot JSON object
        vopts_json = ""
        if (rows(popts) > 0) {
            for (i = 1; i <= rows(popts); i++) {
                if (i > 1) vopts_json = vopts_json + ", "
                vopts_json = vopts_json + `"""' + _json_escape(popts[i,1]) + `"""' + ": " + `"""' + _json_escape(popts[i,2]) + `"""'
            }
        }

        plot_json = `"{"type": ""' + _json_escape(ptype) + `"""'
        if (anyof(("histogram", "kdensity"), ptype)) {
            plot_json = plot_json + `", "var": ""' + _json_escape(yvar) + `"""'
        }
        else if (anyof(("rarea", "rbar", "rspike", "rcap", "rline", "rconnected", "rcapsym",
                        "tsrline"), ptype)) {
            plot_json = plot_json + `", "yvar1": ""' + _json_escape(yvar1) + `"""'
            plot_json = plot_json + `", "yvar2": ""' + _json_escape(yvar2) + `"""'
            plot_json = plot_json + `", "xvar": ""' + _json_escape(xvar) + `"""'
        }
        else if (anyof(("pcspike", "pcarrow", "pcbarrow"), ptype)) {
            string scalar dq2
            dq2 = char(34)
            plot_json = plot_json + ", " + dq2 + "y1var" + dq2 + ": " + dq2 + _json_escape(y1var) + dq2
            plot_json = plot_json + ", " + dq2 + "x1var" + dq2 + ": " + dq2 + _json_escape(x1var) + dq2
            plot_json = plot_json + ", " + dq2 + "y2var" + dq2 + ": " + dq2 + _json_escape(y2var) + dq2
            plot_json = plot_json + ", " + dq2 + "x2var" + dq2 + ": " + dq2 + _json_escape(x2var) + dq2
        }
        else if (ptype == "scatteri") {
            // encode literal coordinate pairs as raw JSON array of [y,x] arrays
            // Each element: [y, x] — varlist is y1 x1 y2 x2 ...
            string scalar vals_json
            real scalar np, pi
            string scalar dq
            dq = char(34)
            vals_json = "["
            np = cols(varlist_words) / 2
            for (pi = 1; pi <= np; pi++) {
                if (pi > 1) vals_json = vals_json + ", "
                vals_json = vals_json + "[" + varlist_words[2*pi-1] + ", " + varlist_words[2*pi] + "]"
            }
            vals_json = vals_json + "]"
            // Embed as raw JSON array (not a quoted string)
            plot_json = plot_json + ", " + dq + "values" + dq + ": " + vals_json
        }
        else if (ptype == "function") {
            string scalar dq3
            dq3 = char(34)
            plot_json = plot_json + ", " + dq3 + "expr" + dq3 + ": " + dq3 + _json_escape(expr_val) + dq3
        }
        else {
            // standard: yvar xvar (scatter, line, tsline, mspline, dropline, etc.)
            plot_json = plot_json + `", "yvar": ""' + _json_escape(yvar) + `"""'
            plot_json = plot_json + `", "xvar": ""' + _json_escape(xvar) + `"""'
        }
        plot_json = plot_json + `", "options": {"' + vopts_json + "}}"

        plots_json = plots_json \ plot_json
    }

    // ---- parse graph-level options  (P1A-09) ----
    if (rows(graph_opts_tokens) > 0) {
        gopts = _parse_options(graph_opts_tokens, 1, rows(graph_opts_tokens))
    }
    else {
        gopts = J(0, 2, "")
    }

    // ---- assemble final JSON  (P1A-17) ----
    // plots array
    string scalar plots_arr
    plots_arr = "["
    for (g = 1; g <= rows(plots_json); g++) {
        if (g > 1) plots_arr = plots_arr + ", "
        plots_arr = plots_arr + plots_json[g, 1]
    }
    plots_arr = plots_arr + "]"

    // graph_options object
    string scalar gopts_str
    gopts_str = "{"
    for (m = 1; m <= rows(gopts); m++) {
        if (m > 1) gopts_str = gopts_str + ", "
        gopts_str = gopts_str + `"""' + _json_escape(gopts[m,1]) + `"""' + ": " + `"""' + _json_escape(gopts[m,2]) + `"""'
    }
    gopts_str = gopts_str + "}"

    json_out = `"{"plots": "' + plots_arr + `", "graph_options": "' + gopts_str
    // add if/in qualifiers  (P1A-18, P1A-19)
    json_out = json_out + `", "if_expr": ""' + _json_escape(if_expr) + `"""'
    json_out = json_out + `", "in_expr": ""' + _json_escape(in_expr) + `"""'
    json_out = json_out + "}"

    return(json_out)
}


// ============================================================
// PUBLIC ENTRY POINT
// dash_parse(input, result_macro)
//
// Called from dash.ado via:
//   mata: dash_parse("`spec'", "dash_json")
// The JSON result is stored in the local macro named by result_macro.
// ============================================================
void dash_parse(string scalar input, string scalar result_macro) {
    string scalar  clean, if_expr, in_expr, json
    string matrix  tokens
    real   scalar  if_pos, in_pos

    // ---- UTF-8 validation  (P1A-16) ----
    if (!_is_utf8(input)) {
        errprintf("dash: input contains non-UTF-8 bytes. Ensure your do-file is saved as UTF-8.\n")
        exit(198)
    }

    // ---- strip leading/trailing whitespace ----
    clean = strtrim(input)

    // ---- extract if/in qualifiers  (P1A-18, P1A-19) ----
    // Strategy: tokenise first, then look for WORD tokens "if" and "in" at
    // depth 0 that appear BEFORE the first parenthesised group or plot type.
    // For simplicity we scan the raw string for " if " and " in " at the end
    // of the spec section (after all plot specs, before the top-level comma).
    if_expr = ""
    in_expr = ""

    // Look for " if " not inside parens or quotes
    // We'll do a simple scan: find " if " as a substring at depth 0
    real scalar pos_if, pos_in, scan_i, scan_d
    string scalar ch2
    pos_if = 0
    pos_in = 0
    scan_d = 0

    real scalar slen
    slen = strlen(clean)
    for (scan_i = 1; scan_i <= slen; scan_i++) {
        ch2 = substr(clean, scan_i, 1)
        if      (ch2 == "(") scan_d = scan_d + 1
        else if (ch2 == ")") {
            if (scan_d > 0) scan_d = scan_d - 1
        }
        else if (ch2 == `"""') {
            // skip over quoted string
            scan_i = scan_i + 1
            while (scan_i <= slen & substr(clean, scan_i, 1) != `"""') scan_i = scan_i + 1
        }
        if (scan_d == 0) {
            if (substr(clean, scan_i, 4) == " if ") pos_if = scan_i
            if (substr(clean, scan_i, 4) == " in ") pos_in = scan_i
        }
    }

    // The LAST occurrence of " if " / " in " at depth 0 is what we want.
    // Extract the conditional/range, then remove from clean.
    // Handle both being present (e.g., "if cond in 1/10").
    real scalar body_end
    body_end = slen

    if (pos_if > 0 & pos_in > 0) {
        if (pos_if < pos_in) {
            // "... if cond in range"
            if_expr = strtrim(substr(clean, pos_if + 4, pos_in - pos_if - 4))
            in_expr = strtrim(substr(clean, pos_in + 4, .))
            body_end = pos_if - 1
        }
        else {
            // "... in range if cond" (unusual but handle)
            in_expr  = strtrim(substr(clean, pos_in + 4, pos_if - pos_in - 4))
            if_expr  = strtrim(substr(clean, pos_if + 4, .))
            body_end = pos_in - 1
        }
    }
    else if (pos_if > 0) {
        if_expr  = strtrim(substr(clean, pos_if + 4, .))
        body_end = pos_if - 1
    }
    else if (pos_in > 0) {
        in_expr  = strtrim(substr(clean, pos_in + 4, .))
        body_end = pos_in - 1
    }

    clean = strtrim(substr(clean, 1, body_end))

    // ---- Pass 1: tokenise ----
    tokens = _tokenize(clean)

    // ---- Pass 2: structural parse ----
    json = _parse_structure(tokens, if_expr, in_expr)

    // ---- store result in Stata local macro ----
    st_local(result_macro, json)
}

end
