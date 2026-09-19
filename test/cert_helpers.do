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

capture mata: mata drop _cert_file_has()

mata:
mata set matastrict off

// Returns 1 if `needle' occurs anywhere in the file at `path', else 0.
// `lower' != 0 compares case-insensitively.  Returns -1 if the file cannot
// be opened, so a caller can tell "absent" from "unreadable" -- a test that
// treats a missing file as "string not found" reports the wrong defect.
real scalar _cert_file_has(string scalar path, string scalar needle,
                           real scalar lower)
{
    real scalar   fh, found
    string scalar line, hay, ndl

    fh = _fopen(path, "r")
    if (fh < 0) return(-1)

    ndl   = lower ? strlower(needle) : needle
    found = 0
    while ((line = fget(fh)) != J(0, 0, "")) {
        hay = lower ? strlower(line) : line
        if (strpos(hay, ndl) > 0) {
            found = 1
            break
        }
    }
    _fclose(fh)
    return(found)
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
