*! extract_alias_spelling_truth.do
*! twoway's own verdict on the spellings dash accepts that
*! test/fixtures/abbrev_truth.json does not settle, measured by running
*! twoway itself.
*!
*!   * bins() and bw(), which dash.ado folds into bin(), bwidth() and
*!     barwidth() -- bw() on the bandwidth plot types and on the bar family;
*!   * sort1(), the name -syntax- gives the argument form of sort();
*!   * clcolor(), clpattern() and clwidth(), twoway options dash honours
*!     that abbrev_truth.json predates, by their full names;
*!   * every plot-type abbreviation dash's expander (_expand_plottype_str in
*!     dash_parse.mata) accepts below twoway's measured minimum, and every
*!     prefix of tsrline, which abbrev_truth.json does not probe.
*!
*! test/test_help_conformance.py reads the result: a spelling dash accepts
*! and twoway does not must be named in dash.sthlp.
*!
*! Output: the JSON file named by the first argument, normally
*! test/fixtures/alias_spelling_truth.json.  Run from a scratch directory,
*! because batch mode writes its .log to the working directory, with the
*! console binary (never the GUI application):
*!
*!   STATATMP=<scratch>/ sh <repo>/scripts/stata_batch.sh -b do \
*!       <repo>/scripts/extract_alias_spelling_truth.do \
*!       <repo>/test/fixtures/alias_spelling_truth.json
*!
*! METHOD
*! A zero return code is not enough: twoway accepts t(abc) and resolves it to
*! t1title().  Each probe is saved to a live-format .gph, and where twoway
*! accepts it, the .gph -- with the echoed command lines, the date and time
*! stamps and the per-run object ids normalised away, exactly as
*! scripts/extract_abbrev_truth.do does -- is compared with the one the full
*! spelling produces.  Identical means the spelling resolved to it.  A full
*! name is compared with the same plot drawn without it instead: accepted
*! AND different means twoway has the option.  Every reference is drawn
*! twice; a reference whose two drawings differ cannot serve as an oracle,
*! and its probes record the return code alone.
*!
*! Stata runs the probes and writes a record file; one trailing python block
*! compares the .gph files and writes the JSON.  It never calls back into
*! Stata.
version 16.0
args outfile
if `"`outfile'"' == "" {
    display as error "usage: do extract_alias_spelling_truth.do <output.json>"
    exit 198
}

clear all
set more off
set graphics off
sysuse auto, clear
generate int t = _n
tsset t

global ZQS_OUT `"`outfile'"'
local work "`c(tmpdir)'dash_alias_spelling_probe"
capture mkdir "`work'"
global ZQS_WORK "`work'"
global ZQS_REC  "`work'/records.txt"
global ZQS_SVER = c(stata_version)
global ZQS_EDIT = c(edition_real)
global ZQS_BORN = c(born_date)
global ZQS_DATE = c(current_date)

tempname rec
file open `rec' using "${ZQS_REC}", write text replace

* Draw one reference twice.  Records: REF|id|rc|path_a|path_b|command
capture program drop zqs_ref
program define zqs_ref
    args rec id cmd
    local pa "${ZQS_WORK}/ref_`id'_a.gph"
    local pb "${ZQS_WORK}/ref_`id'_b.gph"
    // A command with no options of its own needs the comma before nodraw.
    local sep = cond(strpos(`"`cmd'"', ","), " ", ", ")
    set seed 12345
    capture twoway `cmd'`sep'nodraw saving("`pa'", replace)
    local rca = _rc
    sleep 1100
    set seed 12345
    capture twoway `cmd'`sep'nodraw saving("`pb'", replace)
    file write `rec' `"REF|`id'|`rca'|`pa'|`pb'|twoway `cmd'"' _n
end

* One probe.  Records: PROBE|kind|group|spelling|target|refid|rc|path|command
capture program drop zqs_probe
program define zqs_probe
    args rec kind group spelling target refid cmd
    // Named by the reference too: one spelling is probed in several contexts.
    local p "${ZQS_WORK}/probe_`kind'_`refid'_`spelling'.gph"
    local sep = cond(strpos(`"`cmd'"', ","), " ", ", ")
    capture erase "`p'"
    set seed 12345
    // noisily: twoway's own message for a refusal stays in the log.
    display as text `"probe: twoway `cmd'"'
    capture noisily twoway `cmd'`sep'nodraw saving("`p'", replace)
    local rc = _rc
    file write `rec' `"PROBE|`kind'|`group'|`spelling'|`target'|`refid'|`rc'|`p'|twoway `cmd'"' _n
end

* ---- option aliases ------------------------------------------------------
* bins(): twoway_histogram_parse.class declares BINs(), so bins is the full
* name there and bin its minimum -- measured, not assumed.
zqs_ref   `rec' bin_hist   "histogram mpg, bin(5)"
zqs_probe `rec' option bins bins bin bin_hist "histogram mpg, bins(5)"

* bw() on the bandwidth types, against bwidth().
zqs_ref   `rec' bwidth_lpoly "lpoly mpg weight, bwidth(400)"
zqs_probe `rec' option bw bw bwidth bwidth_lpoly "lpoly mpg weight, bw(400)"
zqs_ref   `rec' bwidth_kdens "kdensity mpg, bwidth(2)"
zqs_probe `rec' option bw bw bwidth bwidth_kdens "kdensity mpg, bw(2)"
zqs_ref   `rec' bwidth_lowess "lowess mpg weight, bwidth(0.3)"
zqs_probe `rec' option bw bw bwidth bwidth_lowess "lowess mpg weight, bw(0.3)"

* bw() on the bar family, where dash reads it as barwidth().
zqs_ref   `rec' barwidth_bar "bar mpg weight, barwidth(100)"
zqs_probe `rec' option bw bw barwidth barwidth_bar "bar mpg weight, bw(100)"
zqs_ref   `rec' barwidth_rbar "rbar mpg price weight, barwidth(100)"
zqs_probe `rec' option bw bw barwidth barwidth_rbar "rbar mpg price weight, bw(100)"
zqs_ref   `rec' barwidth_spike "spike mpg weight"
zqs_probe `rec' option bw bw barwidth barwidth_spike "spike mpg weight, bw(100)"
zqs_ref   `rec' barwidth_dot "dot mpg weight"
zqs_probe `rec' option bw bw barwidth barwidth_dot "dot mpg weight, bw(100)"
zqs_ref   `rec' barwidth_hist "histogram mpg"
zqs_probe `rec' option bw bw barwidth barwidth_hist "histogram mpg, bw(2)"

* sort1(): twoway_yxview_parse.class declares SORT SORT1(namelist).
* t is _n: a sort variable with ties is joined in a different order on
* every run (dash.sthlp, Connection order), which no oracle survives.
zqs_ref   `rec' sort_line "line mpg weight, sort(t)"
zqs_probe `rec' option sort1 sort1 sort sort_line "line mpg weight, sort1(t)"

* clcolor(), clpattern(), clwidth(): twoway_yxview_parse.class declares
* CLColor, CLPattern and CLWidth.  Full names, against the plain line.
zqs_ref   `rec' line_plain "line mpg weight"
zqs_probe `rec' fullname clcolor clcolor clcolor line_plain "line mpg weight, clcolor(red)"
zqs_probe `rec' fullname clpattern clpattern clpattern line_plain "line mpg weight, clpattern(dash)"
zqs_probe `rec' fullname clwidth clwidth clwidth line_plain "line mpg weight, clwidth(thick)"

* ---- plot-type abbreviations ---------------------------------------------
* Every prefix dash's expander accepts below twoway's minimum in
* abbrev_truth.json, and every prefix of tsrline.
local pt_area     "ar are"
local pt_bar      "ba"
local pt_spike    "sp spi spik"
local pt_lfit     "lfi"
local pt_qfit     "qfi"
local pt_lowess   "low lowe lowes"
local pt_lpoly    "lpo lpol"
local pt_fpfit    "fp fpf fpfi"
local pt_kdensity "kde kden kdens kdensi kdensit"
local pt_dropline "dr dro drop dropl dropli droplin"
local pt_tsline   "tsl tsli tslin"
local pt_mspline  "msp mspl mspli msplin"
local pt_tsrline  "ts tsr tsrl tsrli tsrlin tsrline"
local v_area     "mpg weight"
local v_bar      "mpg weight"
local v_spike    "mpg weight"
local v_lfit     "mpg weight"
local v_qfit     "mpg weight"
local v_lowess   "mpg weight"
local v_lpoly    "mpg weight"
local v_fpfit    "mpg weight"
local v_kdensity "mpg"
local v_dropline "mpg weight"
local v_tsline   "mpg"
local v_mspline  "mpg weight"
local v_tsrline  "mpg turn"
foreach type in area bar spike lfit qfit lowess lpoly fpfit kdensity dropline tsline mspline tsrline {
    zqs_ref `rec' pt_`type' "`type' `v_`type''"
    foreach s of local pt_`type' {
        zqs_probe `rec' plottype `type' `s' `type' pt_`type' "`s' `v_`type''"
    }
}
file close `rec'

python:
import json
import os
import re

import sfi

REC = sfi.Macro.getGlobal("ZQS_REC")
OUT = sfi.Macro.getGlobal("ZQS_OUT")

_K = re.compile(r"K[0-9a-fA-F]{6,}")
_BANG = re.compile(r"(?m)^\*!.*$")
_CMD = re.compile(r"(?m)^\.(command|date|time) = .*$")


def gph(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, "r", errors="replace") as fh:
        txt = fh.read()
    return _K.sub("K#", _CMD.sub("", _BANG.sub("", txt)))


refs, probes = {}, []
with open(REC, "r", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "REF":
            ta, tb = gph(f[3]), gph(f[4])
            refs[f[1]] = {"rc": int(f[2]), "text": ta,
                          "stable": ta is not None and ta == tb,
                          "command": "|".join(f[5:])}
        elif f[0] == "PROBE":
            probes.append({"kind": f[1], "group": f[2], "spelling": f[3],
                           "target": f[4], "ref": f[5], "rc": int(f[6]),
                           "path": f[7], "command": "|".join(f[8:])})

out = {"options": {}, "plottypes": {}}
for p in probes:
    ref = refs[p["ref"]]
    same = None
    if p["rc"] == 0 and ref["rc"] == 0 and ref["stable"]:
        same = gph(p["path"]) == ref["text"]
    if p["rc"] != 0:
        accepts = False
    elif p["kind"] == "fullname":
        # the reference is the plot without the option: it must differ
        accepts = None if same is None else not same
    else:
        accepts = same          # None: accepted, resolution not verifiable
    row = {"target": p["target"], "context": p["ref"],
           "command": p["command"], "reference": ref["command"],
           "reference_rc": ref["rc"], "reference_stable": ref["stable"],
           "rc": p["rc"], "twoway_accepts": accepts}
    if p["kind"] == "fullname":
        row["differs_from_reference"] = None if same is None else not same
    else:
        row["resolves_to_target"] = same
    if p["kind"] in ("option", "fullname"):
        out["options"].setdefault(p["spelling"], []).append(row)
    else:
        out["plottypes"].setdefault(p["group"], {})[p["spelling"]] = row

for t, rows in out["plottypes"].items():
    ok = [s for s, r in rows.items() if r["twoway_accepts"]]
    rows_min = min(ok, key=len) if ok else None
    out["plottypes"][t] = {"probes": rows, "shortest_accepted": rows_min}

out["_meta"] = {
    "generated_by": "scripts/extract_alias_spelling_truth.do",
    "stata_version": sfi.Macro.getGlobal("ZQS_SVER"),
    "stata_edition": sfi.Macro.getGlobal("ZQS_EDIT"),
    "stata_born_date": sfi.Macro.getGlobal("ZQS_BORN"),
    "run_date": sfi.Macro.getGlobal("ZQS_DATE"),
    "dataset": "sysuse auto, clear; generate int t = _n; tsset t",
    "method": ("Each probe is run as twoway <command> nodraw saving(); rc is "
               "recorded, and where rc is 0 the live-format .gph, with the "
               "*! header lines, the .command/.date/.time lines and the "
               "K<hex> object ids normalised away, is compared with the "
               "reference's.  twoway_accepts is true when rc is 0 and the "
               "two are identical -- for a full-name probe, whose reference "
               "is the plot without the option, when rc is 0 and the two "
               "differ -- false when rc is not 0, and null when rc is 0 but "
               "the reference drawn twice did not normalise to identical "
               "text, so resolution could not be verified."),
}
with open(OUT, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True)
    fh.write("\n")
print("wrote " + OUT)
end
