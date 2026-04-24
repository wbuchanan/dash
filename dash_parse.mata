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
*!   _dash_expand_opts_str(opts_raw, out_macro)
*!       Expand option-key abbreviations in an options string.
*!       E.g. "mc(red) ms(oh)" → "mcolor(red) msymbol(oh)"
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
    real scalar i, len, b, expect, j
    len = strlen(s)
    i   = 1
    while (i <= len) {
        b = ascii(substr(s, i, 1))
        if      (b < 128)              expect = 0
        else if (b >= 194 & b <= 223)  expect = 1
        else if (b >= 224 & b <= 239)  expect = 2
        else if (b >= 240 & b <= 244)  expect = 3
        else                           return(0)
        for (j = 1; j <= expect; j++) {
            if (i + j > len) return(0)
            b = ascii(substr(s, i + j, 1))
            if (b < 128 | b > 191) return(0)
        }
        i = i + expect + 1
    }
    return(1)
}

void _dash_check_utf8(string scalar s) {
    if (!_is_utf8(s)) {
        errprintf("dash: input contains non-UTF-8 bytes. Ensure your do-file is saved as UTF-8.\n")
        exit(198)
    }
}


// ============================================================
// 2. PLOT-TYPE ABBREVIATION EXPANSION
// ============================================================

string scalar _expand_plottype_str(string scalar name) {
    if (name == "sc"  | name == "scatter")      return("scatter")
    if (name == "li"  | name == "line")         return("line")
    if (name == "con" | name == "connected")    return("connected")
    if (name == "ar"  | name == "area")         return("area")
    if (name == "ba"  | name == "bar")          return("bar")
    if (name == "sp"  | name == "spike")        return("spike")
    if (name == "lfi" | name == "lfit")         return("lfit")
    if (name == "qfi" | name == "qfit")         return("qfit")
    if (name == "lfitci")                        return("lfitci")
    if (name == "qfitci")                        return("qfitci")
    if (name == "low" | name == "lowess")        return("lowess")
    if (name == "lpo" | name == "lpol" | name == "lpoly")  return("lpoly")
    if (name == "lpolyci")                       return("lpolyci")
    if (name == "fp"  | name == "fpf" | name == "fpfit")   return("fpfit")
    if (name == "fpfitci")                       return("fpfitci")
    if (name == "hist" | name == "histogram")    return("histogram")
    if (name == "kde"  | name == "kdensity")     return("kdensity")
    if (name == "rarea")                         return("rarea")
    if (name == "rbar")                          return("rbar")
    if (name == "rspike")                        return("rspike")
    if (name == "rcap")                          return("rcap")
    if (name == "rline")                         return("rline")
    if (name == "rconnected")                    return("rconnected")
    if (name == "dot")                           return("dot")
    if (name == "dr" | name == "dropline")       return("dropline")
    if (name == "rcapsym")                       return("rcapsym")
    if (name == "pcspike")                       return("pcspike")
    if (name == "pcarrow")                       return("pcarrow")
    if (name == "pcbarrow")                      return("pcbarrow")
    if (name == "pci")                           return("pci")
    if (name == "pcscatter")                     return("pcscatter")
    if (name == "tsl"  | name == "tsline")       return("tsline")
    if (name == "tsrl" | name == "tsrline")      return("tsrline")
    if (name == "msp"  | name == "mspline")      return("mspline")
    if (name == "mband")                         return("mband")
    if (name == "rscatter")                      return("rscatter")
    if (name == "func" | name == "function")     return("function")
    if (name == "scatteri")                      return("scatteri")
    return("")   // unrecognised
}

void _dash_expand_plottype(string scalar abbrev, string scalar out_macro) {
    st_local(out_macro, _expand_plottype_str(strlower(strtrim(abbrev))))
}


// ============================================================
// 3. OPTION-KEY ABBREVIATION EXPANSION
// ============================================================

// Expand a single option-key abbreviation to its full name.
// Returns the original key if no match (passes through unknown options).
string scalar _expand_optkey(string scalar name) {
    // marker options
    if (name == "mc")    return("mcolor")
    if (name == "ms")    return("msymbol")
    if (name == "msi")   return("msize")
    if (name == "msa")   return("msangle")
    if (name == "mla")   return("mlabel")
    if (name == "mlc")   return("mlabcolor")
    if (name == "mls")   return("mlabsize")
    if (name == "mlp")   return("mlabposition")
    if (name == "mlg")   return("mlabgap")
    if (name == "mlw")   return("mlabwidth")
    if (name == "mfc")   return("mfcolor")
    if (name == "mal")   return("malpha")
    if (name == "m")     return("marker")
    // fill options
    if (name == "fc")    return("fcolor")
    if (name == "fi")    return("fintensity")
    if (name == "fa")    return("falpha")
    if (name == "blc")   return("blcolor")
    if (name == "bfc")   return("bfcolor")
    if (name == "bw")    return("barwidth")
    // line options
    if (name == "lc")    return("lcolor")
    if (name == "lw")    return("lwidth")
    if (name == "lp")    return("lpattern")
    if (name == "lal")   return("lalpha")
    if (name == "fal")   return("falpha")
    // graph-level options
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
    // jitter
    if (name == "jit")   return("jitter")
    if (name == "jse")   return("jseed")
    // dual-axis
    if (name == "yax")   return("yaxis")
    if (name == "xax")   return("xaxis")
    // secondary axis
    if (name == "yti2")  return("ytitle2")
    if (name == "xti2")  return("xtitle2")
    if (name == "yla2")  return("ylabel2")
    if (name == "xla2")  return("xlabel2")
    if (name == "ysc2")  return("yscale2")
    if (name == "xsc2")  return("xscale2")
    // scheme
    if (name == "sch")   return("scheme")
    // colorvar
    if (name == "cv")    return("colorvar")
    if (name == "colv")  return("colorvar")
    if (name == "colpal") return("colpalette")
    // smoother options
    if (name == "bwid")  return("bwidth")
    if (name == "deg")   return("degree")
    // passthrough: full names and unknown abbreviations
    return(name)
}

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
void _dash_expand_opts_str(string scalar opts_raw, string scalar out_macro) {
    real scalar i, len, depth, in_dq, in_cq, c_code
    string scalar result, word_buf, ch

    result   = ""
    word_buf = ""
    depth    = 0
    in_dq    = 0
    in_cq    = 0
    len      = strlen(opts_raw)
    i        = 1

    while (i <= len) {
        ch     = substr(opts_raw, i, 1)
        c_code = ascii(ch)

        // ---- inside double-quoted string ----
        if (in_dq) {
            result = result + ch
            if (c_code == 34) in_dq = 0
            i++
            continue
        }

        // ---- inside compound-quoted string `"..."' ----
        if (in_cq) {
            result = result + ch
            if (c_code == 34 & i + 1 <= len & ascii(substr(opts_raw, i+1, 1)) == 39) {
                result = result + "'"
                i      = i + 2
                in_cq  = 0
            }
            else i++
            continue
        }

        // ---- start double-quote ----
        if (c_code == 34 & depth == 0) {
            // flush any accumulated word as a bare flag
            if (word_buf != "") {
                result   = result + _expand_optkey(strlower(word_buf))
                word_buf = ""
            }
            result = result + ch
            in_dq  = 1
            i++
            continue
        }

        // ---- start compound-quote `" ----
        if (c_code == 96 & depth == 0 &
            i + 1 <= len & ascii(substr(opts_raw, i+1, 1)) == 34) {
            if (word_buf != "") {
                result   = result + _expand_optkey(strlower(word_buf))
                word_buf = ""
            }
            result = result + ch
            in_cq  = 1
            i++
            continue
        }

        if (depth == 0) {
            // open paren: the accumulated word is an option key
            if (c_code == 40) {
                if (word_buf != "") {
                    result   = result + _expand_optkey(strlower(word_buf)) + "("
                    word_buf = ""
                }
                else {
                    result = result + "("
                }
                depth++
                i++
                continue
            }
            // whitespace: flush word buffer as bare flag
            if (c_code == 32 | c_code == 9) {
                if (word_buf != "") {
                    result   = result + _expand_optkey(strlower(word_buf))
                    word_buf = ""
                }
                result = result + " "
                i++
                continue
            }
            // comma at depth 0: shouldn't normally appear here, but pass through
            if (c_code == 44) {
                if (word_buf != "") {
                    result   = result + _expand_optkey(strlower(word_buf))
                    word_buf = ""
                }
                result = result + ","
                i++
                continue
            }
            // any other character: accumulate into word buffer
            word_buf = word_buf + ch
            i++
        }
        else {
            // inside parentheses: copy verbatim, track depth
            if      (c_code == 40) depth++
            else if (c_code == 41) {
                depth--
                if (depth == 0) {
                    result = result + ")"
                    i++
                    continue
                }
            }
            result = result + ch
            i++
        }
    }

    // flush any remaining word
    if (word_buf != "") {
        result = result + _expand_optkey(strlower(word_buf))
    }

    st_local(out_macro, strtrim(result))
}


// ============================================================
// 4. COMMA POSITION FINDER
// ============================================================

// Return the character position (1-based) of the first comma at
// depth 0 (outside parens and quotes), or 0 if none found.
real scalar _first_comma_pos(string scalar input) {
    real scalar i, len, depth, in_dq, in_cq, c_code
    string scalar ch

    len   = strlen(input)
    depth = 0
    in_dq = 0
    in_cq = 0
    i     = 1

    while (i <= len) {
        ch     = substr(input, i, 1)
        c_code = ascii(ch)

        if (in_dq) {
            if (c_code == 34) in_dq = 0
            i++; continue
        }
        if (in_cq) {
            if (c_code == 34 & i+1 <= len & ascii(substr(input, i+1, 1)) == 39) {
                i = i + 2; in_cq = 0
            }
            else i++
            continue
        }
        if (c_code == 34 & depth == 0) {
            in_dq = 1
            i++
            continue
        }
        if (c_code == 96 & depth == 0 &
            i+1 <= len & ascii(substr(input, i+1, 1)) == 34) {
            in_cq = 1; i = i + 2; continue
        }
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
    real   scalar  i, len, depth, in_dq, in_cq, c_code
    real   scalar  seg_start, n_segs
    string scalar  ch, seg_text, trimmed
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
        i         = 1

        while (i <= len) {
            ch     = substr(trimmed, i, 1)
            c_code = ascii(ch)

            if (in_dq) {
                if (c_code == 34) in_dq = 0
                i++; continue
            }
            if (in_cq) {
                if (c_code == 34 & i+1 <= len & ascii(substr(trimmed, i+1, 1)) == 39) {
                    i = i + 2; in_cq = 0
                }
                else i++
                continue
            }
            if (c_code == 34) {
                in_dq = 1
                i++
                continue
            }
            if (c_code == 96 & i+1 <= len & ascii(substr(trimmed, i+1, 1)) == 34) {
                in_cq = 1; i = i + 2; continue
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
            else if (c_code == 44 & depth == 0) {
                // top-level comma after all () groups → graph opts
                graph_opts_raw = strtrim(substr(trimmed, i + 1, .))
                break
            }
            i++
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
            ch     = substr(trimmed, i, 1)
            c_code = ascii(ch)

            if (in_dq) {
                if (c_code == 34) in_dq = 0
                i++; continue
            }
            if (in_cq) {
                if (c_code == 34 & i+1 <= len & ascii(substr(trimmed, i+1, 1)) == 39) {
                    i = i + 2; in_cq = 0
                }
                else i++
                continue
            }
            if (c_code == 34 & depth == 0) {
                in_dq = 1
                i++
                continue
            }
            if (c_code == 96 & depth == 0 &
                i+1 <= len & ascii(substr(trimmed, i+1, 1)) == 34) {
                in_cq = 1; i = i + 2; continue
            }
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
// "var", "yvar1", "yvar2", "y1var", "x1var", "y2var", "x2var" values
// into a space-separated varlist stored in out_macro.
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
               char(34)+"colorvar"+char(34)+":")
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

    raw       = st_local("0")   // raw command string
    lraw      = strlower(raw)
    n         = strlen(raw)
    result    = ""
    remaining = ""
    i         = 1

    while (i <= n) {
        // Attempt to match a filter keyword at position i.
        // Accepted abbreviated forms: filt(4), filte(5), filter(6).
        matched = 0
        klen    = 0

        if (i + 5 <= n & substr(lraw, i, 6) == "filter") {
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
                while (k <= n & depth > 0) {
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

        remaining = remaining + substr(raw, i, 1)
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
        else if (ch == "\\") {
            // Escape sequence — peek at next character
            if (pos + 1 <= n) {
                ch = substr(json_str, pos + 1, 1)
                if      (ch == char(34)) value = value + char(34)
                else if (ch == "\\")     value = value + "\\"
                else if (ch == "n")      value = value + char(10)
                else if (ch == "r")      value = value + char(13)
                else if (ch == "t")      value = value + char(9)
                else                     value = value + "\\" + ch
                pos = pos + 2
            }
            else {
                // Trailing backslash with no next char — keep it
                value = value + "\\"
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

end


