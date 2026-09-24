*! cert_helpers.do — shared helpers for the dash certification scripts.
*!
*! WHY THIS EXISTS
*!
*! Every end-to-end script needs to ask "does the generated dashboard contain
*! this string?".  They all did it the same way:
*!
*!     file read `fh' ln
*!     while r(eof) == 0 {
*!         if strpos(`"`ln'"', "bokeh") > 0 ...
*!
*! That cannot work.  A line of Bokeh's output is JSON full of " characters,
*! and sequences such as "' or `" inside it terminate the compound quotes the
*! macro is expanded in.  Measured: five of the six failing scripts died with
*! "too few quotes" and one with "unknown function ()", and the plain-quoted
*! variant in test_e2e_single died with r(111) on the word "Security" from
*! the page.  The content was being parsed as Stata code.
*!
*! Mata strings are values, not macro text, so the same search in Mata cannot
*! be broken by anything the file contains.  cert_file_has() reads the file
*! and returns 0/1; nothing from the file is ever expanded.
*!
*! Usage:
*!     do "cert_helpers.do"
*!     cert_file_has "`outpath'", needle("bokeh") lower
*!     assert r(found) == 1
*!
*!     cert_log_has "`logfile'", needle("global dash_max_by_groups")
*!     assert r(found) == 1          // r(count): how many logical lines
*!
*!     cert_file_count "`outpath'", needle(`""name":"Figure""')
*!     assert r(count) == 3
*!
*! cert_file_has searches a file's bytes; cert_log_has searches the TEXT of
*! a Stata log, with the log's own wrapping undone.  Search a log with
*! cert_log_has: Stata wraps a log line at c(linesize), anywhere, and a
*! Python warning starts with the path to dash_render.py, so where a message
*! breaks depends on where the checkout lives (see _cert_log_count).
*! cert_file_count returns how many times a needle occurs, for a check that
*! must be exact rather than "at least one".  test_conformance.cscript C-00
*! holds all three to what they claim.

// Keep every dashboard this suite builds out of a browser window.
// run_all_cscripts.do sets this global too, but `cscript' -- the first line
// of every script -- drops EVERY global macro (measured 23sep2026: `global
// dash_nobrowser 1' then `cscript "probe"' left it empty; `clear all' does
// not drop it), so the runner's setting never reached the scripts, and a
// dash build without its own nobrowser option would have opened a window
// per build.  Scripts load this file straight after `cscript'; one that does
// not sets the global itself (test_cscript_hygiene.py checks both).
global dash_nobrowser 1

capture mata: mata drop _cert_file_has()
capture mata: mata drop _cert_read()
capture mata: mata drop _cert_log_count()
capture mata: mata drop _cert_file_count()

mata:
mata set matastrict off

// Reads the whole of the file at `path' into `text' and returns 1, or
// returns 0 if the file cannot be opened.
//
// In one piece, not line by line: fget() hands back a line longer than
// 32,768 characters as pieces of 32,768 (measured 24sep2026: a line of
// 80,006 came back as 32,768 + 32,768 + 14,470), and a saved dashboard
// holds lines of about 100,000 characters.  A needle that straddled a piece
// boundary was never seen, so a presence check could fail and an absence
// check -- a payload that must not reach the page -- passed without having
// looked at those bytes.
real scalar _cert_read(string scalar path, string scalar text)
{
    real scalar   fh
    string scalar piece

    fh = _fopen(path, "r")
    if (fh < 0) return(0)
    text = ""
    while ((piece = fread(fh, 1048576)) != J(0, 0, "")) text = text + piece
    fclose(fh)
    return(1)
}

// Returns 1 if `needle' occurs anywhere in the file at `path', else 0.
// `lower' != 0 compares case-insensitively.  Returns -1 if the file cannot
// be opened, so a caller can tell "absent" from "unreadable" -- a test that
// treats a missing file as "string not found" reports the wrong defect.
real scalar _cert_file_has(string scalar path, string scalar needle,
                           real scalar lower)
{
    string scalar text

    if (!_cert_read(path, text)) return(-1)
    if (lower) return(strpos(strlower(text), strlower(needle)) > 0)
    return(strpos(text, needle) > 0)
}

// The number of logical lines of the Stata log at `path' that contain
// `needle', or -1 if the file cannot be opened.
//
// A text log wraps a line longer than c(linesize) and starts each
// continuation with "> ", at the column, mid-word included (measured
// 24sep2026: "... Set global da" / "> sh_max_by_groups to draw more").  A
// Python warning reaches the log as "<path to dash_render.py>:<line>:
// UserWarning: <message>", so where its message breaks depends on where the
// checkout lives: searched line by line, a presence check failed in a long
// checkout path (test_resource_limits.cscript RL-06, in a worktree) and an
// absence check could pass whatever the log said.  Here each logical line
// is rebuilt -- its continuations appended without their "> " -- and
// searched whole.  A physical line fget() returns in 32,768-character
// pieces (see _cert_read) is rebuilt too.
real scalar _cert_log_count(string scalar path, string scalar needle,
                            real scalar lower)
{
    real scalar   fh, n, piece
    string scalar line, full, ndl

    fh = _fopen(path, "r")
    if (fh < 0) return(-1)
    ndl   = lower ? strlower(needle) : needle
    n     = 0
    full  = ""
    piece = 0
    while ((line = fget(fh)) != J(0, 0, "")) {
        if (piece | substr(line, 1, 2) == "> ") {
            full = full + (piece ? line : substr(line, 3, .))
        }
        else {
            n = n + (strpos(lower ? strlower(full) : full, ndl) > 0)
            full = line
        }
        piece = (strlen(line) == 32768)
    }
    n = n + (strpos(lower ? strlower(full) : full, ndl) > 0)
    fclose(fh)
    return(n)
}

// The number of times `needle' occurs in the file at `path', counted
// without overlap, or -1 if the file cannot be opened.
real scalar _cert_file_count(string scalar path, string scalar needle)
{
    real scalar   n, p, k
    string scalar text

    if (!_cert_read(path, text)) return(-1)
    k = strlen(needle)
    if (k == 0) return(0)
    n = 0
    while ((p = strpos(text, needle)) > 0) {
        n = n + 1
        text = substr(text, p + k, .)
    }
    return(n)
}
end

capture program drop cert_file_has
program define cert_file_has, rclass
    version 16.0
    syntax anything(name=fpath id="file path"), Needle(string) [Lower]

    // Strip the quotes -syntax- leaves on the path.
    local fpath = subinstr(`"`fpath'"', `"""', "", .)
    local lc = cond("`lower'" != "", 1, 0)

    tempname res
    mata: st_numscalar("`res'", ///
        _cert_file_has(st_local("fpath"), st_local("needle"), `lc'))

    if scalar(`res') < 0 {
        display as error "cert_file_has: cannot open `fpath'"
        exit 603
    }
    return scalar found = scalar(`res')
end

// cert_log_has: cert_file_has for a Stata log, with its wrapping undone.
// r(found) is 0/1 and r(count) the number of logical lines holding the
// needle, for a check that must be exact ("one report, and it is this").
capture program drop cert_log_has
program define cert_log_has, rclass
    version 16.0
    syntax anything(name=fpath id="log path"), Needle(string) [Lower]

    local fpath = subinstr(`"`fpath'"', `"""', "", .)
    local lc = cond("`lower'" != "", 1, 0)

    tempname res
    mata: st_numscalar("`res'", ///
        _cert_log_count(st_local("fpath"), st_local("needle"), `lc'))

    if scalar(`res') < 0 {
        display as error "cert_log_has: cannot open `fpath'"
        exit 603
    }
    return scalar count = scalar(`res')
    return scalar found = scalar(`res') > 0
end

// cert_file_count: how many times a needle occurs in a file, in r(count).
capture program drop cert_file_count
program define cert_file_count, rclass
    version 16.0
    syntax anything(name=fpath id="file path"), Needle(string)

    local fpath = subinstr(`"`fpath'"', `"""', "", .)

    tempname res
    mata: st_numscalar("`res'", ///
        _cert_file_count(st_local("fpath"), st_local("needle")))

    if scalar(`res') < 0 {
        display as error "cert_file_count: cannot open `fpath'"
        exit 603
    }
    return scalar count = scalar(`res')
end
