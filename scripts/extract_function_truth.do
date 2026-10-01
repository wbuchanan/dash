*! extract_function_truth.do
*! WP-29 section 04 (P0.6): twoway function ground truth for
*! test/fixtures/function_expr_truth.json.
*!
*! WHY THIS EXISTS
*!
*! dash used to evaluate a function layer's expression itself, in Python,
*! and got Stata's grammar wrong (^ folded right to left, pi and e accepted,
*! / and * grouped Python's way).  P0.6 makes Stata evaluate it, through the
*! generator twoway function itself calls (twoway__function_gen).  The
*! renderers' tests need what twoway actually draws -- its serset values --
*! and what the generator returns (r(min), r(delta) and y in generator
*! order) for a battery of data-free expressions, together with twoway's
*! return code for the ones it refuses.  Data-, RNG- and estimate-dependent
*! expressions are not here: their answer depends on the session, so the
*! certification scripts compare them live (test_parser.cscript FX-01..,
*! test_wp29_truth.cscript FX-20..).
*!
*! Output: test/fixtures/function_expr_truth.json
*!
*! Run with (the script sets its own directories, so it is handed to the
*! wrapper directly; CLAUDE.md rule 10):
*!
*!   scripts/stata_slot.sh /tmp/dash-s04 \
*!     /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_function_truth.do
*!
*! METHOD
*!
*! Each probe is a line `zf <id> <n> "<lo hi>" <text>' run on an empty
*! dataset, where <text> is written `y = <e>'.  zf
*!   1. runs `capture twoway function <text>, range(<lo hi>) n(<n>) nodraw'
*!      and keeps its rc;
*!   2. on rc 0 reads twoway's serset (`serset set' on
*!      .Graph.plotregion1.plot1.serset.id, then `serset use': variable 1 is
*!      y, variable 2 is x) -> serset_x, serset_y;
*!   3. on rc 0 runs the generator itself under preserve with tempvars,
*!      `twoway__function_gen <text>, range(<lo hi>) x(x) n(<n>)
*!      generate(fy fx)' -> x0 = r(min), dx = r(delta), gen_y in generator
*!      order.
*! Every number is written %24.17g (it reads back to the same double), with
*! a missing value written null.  One tab-separated record per probe is
*! written by Mata fput, never by `file write' of user text.  The trailing
*! python: block reads the record file and writes the fixture; it never
*! calls back into Stata, never uses a shell, and spells a backtick \x60.
*! ---------------------------------------------------------------------------

version 19
clear all
set graphics off
set more off
set linesize 200

// <repo> is the tree under test: the main checkout.  A section agent
// developing in its own worktree points this at that worktree while it
// runs there, and restores this line before committing.
global ZF_REPO "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
global ZF_OUT  "${ZF_REPO}/test/fixtures/function_expr_truth.json"

local scratch "`c(tmpdir)'dash_function_probe"
capture mkdir "`scratch'"
global ZF_REC "`scratch'/function_records.txt"
capture erase "${ZF_REC}"

global ZF_SVER = c(stata_version)
global ZF_BORN = c(born_date)
global ZF_DATE = c(current_date)

// ---------------------------------------------------------------------------
// Provenance stamp (D12), as extract_text_truth.do captures it: `shell'
// writes the commit into a file and the do-file reads the file back.
// ---------------------------------------------------------------------------
tempfile zfgitrev
quietly shell git -C "${ZF_REPO}" rev-parse HEAD > "`zfgitrev'"
tempname zfgfh
file open `zfgfh' using "`zfgitrev'", read text
file read `zfgfh' zfgitline
file close `zfgfh'
global ZF_COMMIT = trim(`"`zfgitline'"')
capture assert ustrregexm(`"${ZF_COMMIT}"', "^[0-9a-f]{40}$")
if _rc {
    display as error "extract_function_truth.do: git rev-parse HEAD did not print a 40-character commit: ${ZF_COMMIT}"
    exit 498
}

mata:
// %24.17g text of each value, null for a missing value, joined by commas.
string scalar _zf_nums(real colvector v)
{
    string colvector s
    real scalar i
    s = J(rows(v), 1, "")
    for (i = 1; i <= rows(v); i++) {
        if (v[i] >= .) s[i] = "null"
        else s[i] = strtrim(strofreal(v[i], "%24.17g"))
    }
    return(invtokens(s', ","))
}
void _zf_put(string scalar line)
{
    real scalar fh
    fh = fopen(st_global("ZF_REC"), "a")
    fput(fh, line)
    fclose(fh)
}
end

capture program drop zf
program define zf
    version 19
    gettoken id 0 : 0
    gettoken n 0 : 0
    gettoken rng 0 : 0
    local text = strtrim(`"`macval(0)'"')
    clear
    capture twoway function `macval(text)', range(`rng') n(`n') nodraw
    local rc = _rc
    local sx ""
    local sy ""
    local x0 ""
    local dx ""
    local gy ""
    if `rc' == 0 {
        serset set `.Graph.plotregion1.plot1.serset.id'
        preserve
        serset use, clear
        mata: st_local("sy", _zf_nums(st_data(., 1)))
        mata: st_local("sx", _zf_nums(st_data(., 2)))
        restore
        clear
        preserve
        tempvar fy fx
        twoway__function_gen `macval(text)', range(`rng') x(x) n(`n') generate(`fy' `fx')
        mata: st_local("x0", _zf_nums(st_numscalar("r(min)")))
        mata: st_local("dx", _zf_nums(st_numscalar("r(delta)")))
        mata: st_local("gy", _zf_nums(st_data((1, `n'), "`fy'")))
        restore
    }
    mata: _zf_put(invtokens((st_local("id"), st_local("text"), st_local("rng"), ///
        st_local("n"), st_local("rc"), st_local("x0"), st_local("dx"), ///
        st_local("gy"), st_local("sx"), st_local("sy")), char(9)))
    display as text "probe `id' rc=`rc'"
end

// --- power and sign
zf pw01 3 "0 2" y = 2^3^x
zf pw02 3 "0 2" y = (2^3)^x
zf pw03 3 "0 2" y = 2^(3^x)
zf pw04 3 "0 2" y = 2^3^2
zf pw05 3 "0 2" y = x^x^x
zf pw06 3 "0 2" y = x^2^-1
zf pw07 3 "0 2" y = x^2^0.5
zf pw08 3 "0 2" y = x^3^0.5
zf pw09 3 "0 2" y = x^-1^-1
zf pw10 3 "0 2" y = 2^-1
zf pw11 3 "0 2" y = 2^-x
zf pw12 3 "0 2" y = 2^-1^2
zf pw13 3 "0 2" y = 2^-x^2
zf pw14 3 "0 2" y = -2^-2^-2
zf pw15 3 "0 2" y = 2^-2^-1
zf pw16 3 "0 2" y = 2^+1
zf pw17 3 "0 2" y = 2^ - x
// --- unary
zf un01 3 "0 2" y = -2^2
zf un02 3 "0 2" y = -x^2
zf un03 3 "0 2" y = (-x)^2
zf un04 3 "0 2" y = -(-x)^2
zf un05 3 "0 2" y = -x^x
zf un06 3 "0 2" y = -x^-2
zf un07 3 "0 2" y = -x^-x^-1
zf un08 3 "0 2" y = - -x
zf un09 3 "0 2" y = --x
zf un10 3 "0 2" y = 2*-x
zf un11 3 "0 2" y = x*-2^2
zf un12 3 "0 2" y = 3-2^2
zf un13 3 "0 2" y = 2^x*3
zf un14 3 "0 2" y = 2*x^3
zf un15 3 "0 2" y = 2--x
zf un16 3 "0 2" y = 2/-x
// --- precedence
zf pr01 3 "0 2" y = 0.1*3/0.3
zf pr02 3 "0 2" y = 1e16+1-2
zf pr03 3 "0 2" y = 1+0.1-0.7
zf pr04 3 "0 2" y = 1e16+1+1
zf pr05 3 "0 2" y = 0.1*0.7*0.3
zf pr06 3 "0 2" y = 10-2-3
zf pr07 3 "0 2" y = 100/10/5
zf pr08 3 "0 2" y = x/2*3
zf pr09 3 "0 2" y = x-1+2
// --- missing values
zf ms01 3 "0 2" y = 0^0
zf ms02 3 "0 2" y = 0^-1
zf ms03 3 "0 2" y = (-8)^(1/3)
zf ms04 3 "0 2" y = (-2)^x
zf ms05 3 "0 2" y = .
zf ms06 3 "0 2" y = x^.
zf ms07 3 "0 2" y = (0^-1)^0+x
zf ms08 3 "0 2" y = 1/(1/0)+x
zf ms09 3 "0 2" y = exp(-exp(1000))+x
// --- literals
zf lt01 3 "0 2" y = 1e3*x
zf lt02 3 "0 2" y = .5*x
zf lt03 3 "0 2" y = 5.*x
// --- functions
zf fn01 3 "0 2" y = sqrt(x-1)
zf fn02 3 "0 2" y = log(x)
zf fn03 3 "0 2" y = log10(x)
zf fn04 3 "0 2" y = exp(x)
zf fn05 3 "0 2" y = sin(x)
zf fn06 3 "0 2" y = cos(x)
zf fn07 3 "0 2" y = tan(x)
zf fn08 3 "0 2" y = abs(-x)
zf fn09 3 "0 2" y = floor(x/2)
zf fn10 3 "0 2" y = ceil(x/2)
// --- outside the fallback
zf ou01 3 "0 2" y = _pi*x
zf ou02 3 "0 2" y = c(pi)*x
zf ou03 3 "0 2" y = normalden(x)
zf ou04 3 "0 2" y = ln(x)
zf ou05 3 "0 2" y = 1.8X+01*x
zf ou06 3 "0 2" y = (x>1)*x
zf ou07 3 "0 2" y = max(x,1)
// --- overflow towers over range(1 2) n(5)
zf tw01 5 "1 2" y = 9^9^9^9
zf tw02 5 "1 2" y = x^9^9^9
zf tw03 5 "1 2" y = x*9^9^9
zf tw04 5 "1 2" y = 2^10000000
zf tw05 5 "1 2" y = 2^200000
// --- grids
zf gr01 300 "0 1" y = x+1
zf gr02 301 "-3.7 11.2" y = x
zf gr03 3 "0 0.00001" y = x/3
zf gr04 7 "0 1e-5" y = 1/x
zf gr05 3 "0 0.123456789012345678" y = x
zf gr06 3 "2 0" y = x^2
zf gr07 10000 "-100 100" y = sin(x)/x
// --- refusals (rc only)
zf rf01 3 "0 2" y = pi*x
zf rf02 3 "0 2" y = e*x
zf rf03 3 "0 2" y = pi
zf rf04 3 "0 2" y = e
zf rf05 3 "0 2" y = PI
zf rf06 3 "0 2" y = E
zf rf07 3 "0 2" y = x**2
zf rf08 3 "0 2" y = x%2
zf rf09 3 "0 2" y = x//1
zf rf10 3 "0 2" y = +x
zf rf11 3 "0 2" y = 2*+x
zf rf12 3 "0 2" y = (+x)
zf rf13 3 "0 2" y = x^
zf rf14 3 "0 2" y = 2^^x
zf rf15 3 "0 2" y = ｓｉｎ(x)
zf rf16 3 "0 2" y = 2x
zf rf17 3 "0 2" y = sin(x,1)
zf rf18 3 "0 2" y = sin (x)
zf rf19 3 "0 2" y = nosuch(x)
zf rf20 3 "0 2" y = strlen("'x")
local long "x"
forvalues i = 1/600 {
    local long "`long' + sin(x)"
}
zf rf21 3 "0 2" y = `long'
local chain "x"
forvalues i = 2/800 {
    local chain "`chain'+x"
}
zf rf22 3 "0 2" y = `chain'

// ---------------------------------------------------------------------------
// Write the fixture.
// ---------------------------------------------------------------------------
python:
import json
from sfi import Macro

rec_path = Macro.getGlobal("ZF_REC")
out_path = Macro.getGlobal("ZF_OUT")

def nums(text):
    if text == "":
        return []
    return [None if t == "null" else t for t in text.split(",")]

def one(text):
    v = nums(text)
    return v[0] if v else None

probes = []
with open(rec_path, encoding="utf-8") as fh:
    for line in fh:
        line = line.rstrip("\n")
        if not line:
            continue
        f = line.split("\t")
        if len(f) != 10:
            raise SystemExit("bad record: %r" % line[:80])
        probes.append({
            "id": f[0], "expr": f[1], "range": f[2], "n": int(f[3]),
            "rc": int(f[4]), "x0": one(f[5]), "dx": one(f[6]),
            "gen_y": nums(f[7]), "serset_x": nums(f[8]),
            "serset_y": nums(f[9]),
        })

meta = {
    "stata_version": Macro.getGlobal("ZF_SVER"),
    "born_date": Macro.getGlobal("ZF_BORN"),
    "extracted": Macro.getGlobal("ZF_DATE"),
    "dash_commit": Macro.getGlobal("ZF_COMMIT"),
    "method": ("twoway function <text>, range() n() nodraw: rc and serset "
               "(variable 1 y, variable 2 x); twoway__function_gen <text>, "
               "range() x(x) n() generate(fy fx) under preserve: x0 = r(min), "
               "dx = r(delta), gen_y in generator order; numbers %24.17g "
               "text, missing null"),
}
with open(out_path, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "probes": probes}, fh, indent=2,
              sort_keys=True, ensure_ascii=False)
    fh.write("\n")
print("wrote %d probes to %s" % (len(probes), out_path))
end
