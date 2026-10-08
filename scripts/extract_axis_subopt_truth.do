*! extract_axis_subopt_truth.do
*! twoway's axis look sub-options, measured from Stata itself (WP-30
*! P1.18a, section 31): nolabels, noticks, labcolor(), tlength(),
*! tposition() and angle() on the label and tick options; off, noline,
*! lcolor(), lwidth(), lpattern(), alt and titlegap() on the scale options;
*! their second-axis and by() forms; and twoway's refusals, in order.
*!
*! Output: test/fixtures/axis_subopt_truth.json
*!
*! Run (Stata only through the slot wrapper, never the GUI):
*!
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_axis_subopt_truth.do
*!
*! METHOD.  Every probe runs under capture noisily inside its own text log
*! (drawn, never nodraw unless its id says so), so the first message line
*! is read back from that log.  For an rc-0 probe one record line holds,
*! for yaxis1, xaxis1 and (when present) yaxis2, these .Graph members (of
*! .Graph.graphs[1] under by()): draw_view.istrue,
*! style.majorstyle.tickstyle.{show_labels.istrue, show_ticks.istrue,
*! length.val, position.stylename, textstyle.color.rgb},
*! style.majorstyle.tickangle.val, style.linestyle.{color.rgb, width.val,
*! pattern.stylename}, position.stylename and style.title_gap.val; the
*! graph is exported to SVG.  The trailing python: block reads the record
*! file, the logs and the SVGs (scripts/svg_truth.py) and writes the JSON;
*! it never calls Stata and spells a backtick \x60.

clear all
* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_axis_subopt_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
    exit 198
}
while strlen(`"`repo'"') > 1 & inlist(substr(`"`repo'"', -1, 1), "/", char(92)) {
    local repo = substr(`"`repo'"', 1, strlen(`"`repo'"') - 1)
}
capture confirm file `"`repo'/dash.ado"'
local _zr_rc = _rc
capture confirm file `"`repo'/test/run_all_cscripts.do"'
if `_zr_rc' | _rc {
    local _zr_show = substr(`"`repo'"', 1, 200)
    display as error `"extract_axis_subopt_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
adopath ++ "`repo'/"
global dash_nobrowser 1
set graphics off
set more off
set linesize 255
version 19
sysuse auto, clear

global AXL_REPO "`repo'"
global AXL_META_VERSION = c(stata_version)
global AXL_META_BORN "`c(born_date)'"
global AXL_META_DATE "`c(current_date)'"
global AXL_META_SCHEME "`c(scheme)'"
tempfile gh
capture shell cd "`repo'" && git rev-parse HEAD > "`gh'"
global AXL_META_COMMIT ""
capture confirm file "`gh'"
if !_rc {
    tempname fh
    file open `fh' using "`gh'", read text
    file read `fh' line
    file close `fh'
    global AXL_META_COMMIT "`line'"
}

local work "`c(tmpdir)'/dash_axl_probe"
capture mkdir "`work'"
global AXL_WORK "`work'"
global AXL_REC "`work'/axl_records.txt"
capture erase "${AXL_REC}"

capture program drop _axl_members
program _axl_members
    version 19
    // _axl_members <id> <root>: one record per axis of .Graph<root>
    args id root
    foreach ax in yaxis1 xaxis1 yaxis2 {
        local o ".Graph`root'.`ax'"
        local dv "``o'.draw_view.istrue'"
        if "`dv'" == "" continue
        local t "`o'.style.majorstyle.tickstyle"
        local r "M|`id'|`ax'|`dv'|``t'.show_labels.istrue'|``t'.show_ticks.istrue'"
        local r "`r'|``t'.length.val'|``t'.position.stylename'|``t'.textstyle.color.rgb'"
        local r "`r'|``o'.style.majorstyle.tickangle.val'|``o'.style.linestyle.color.rgb'"
        local r "`r'|``o'.style.linestyle.width.val'|``o'.style.linestyle.pattern.stylename'"
        local r "`r'|``o'.position.stylename'|``o'.style.title_gap.val'"
        file write axlrec `"`r'"' _n
    }
end

capture program drop _axl_probe
program _axl_probe
    version 19
    // _axl_probe <id> <plots> <scheme> `"<options>"'
    args id plots scheme opts
    local S "scatter mpg weight"
    local Y2 "(scatter mpg weight) (scatter price weight, yaxis(2) xaxis(2))"
    if "`plots'" == "S"      local cmd "twoway `S', `opts'"
    if "`plots'" == "Y2"     local cmd "twoway `Y2', `opts'"
    if "`plots'" == "BY"     local cmd "twoway `S', by(foreign) `opts'"
    if "`plots'" == "Y2BY"   local cmd "twoway `Y2', by(foreign) `opts'"
    if "`plots'" == "SEG400" local cmd "twoway (scatter mpg weight, ylabel(, angle(400))), `opts'"
    if "`plots'" == "SEG0"   local cmd "twoway (scatter mpg weight, ylabel(, angle(0))), `opts'"
    if "`plots'" == "SEGLW"  local cmd "twoway (scatter mpg weight, yscale(lw(-1))), `opts'"
    if "`scheme'" != "" local cmd "`cmd' scheme(`scheme')"
    // Files are named by the probe's number: ids such as ang_V and ang_v
    // differ only in case, which a case-insensitive file system merges.
    global AXL_N = ${AXL_N} + 1
    local stem "p${AXL_N}"
    sysuse auto, clear
    capture graph drop _all
    capture log close _axl
    quietly log using "${AXL_WORK}/`stem'.log", text replace name(_axl)
    capture noisily `cmd'
    local rc = _rc
    quietly log close _axl
    file write axlrec `"P|`id'|`rc'|`scheme'|`stem'|`cmd'"' _n
    if `rc' == 0 & strpos("`id'", "nodraw") == 0 {
        local root ""
        if strpos("`plots'", "BY") local root ".graphs[1]"
        _axl_members `id' "`root'"
        capture graph export "${AXL_WORK}/`stem'.svg", replace
    }
    capture graph drop _all
end

global AXL_N = 0
file open axlrec using "${AXL_REC}", write text replace
_axl_probe base_st S "" `""'
_axl_probe base_s2 S "s2color" `""'
_axl_probe base_econ S "economist" `""'
_axl_probe lab_nolabels S "" `"ylabel(, nolabels)"'
_axl_probe lab_nolab S "" `"ylabel(, nolab)"'
_axl_probe lab_noticks S "" `"ylabel(, noticks)"'
_axl_probe lab_notick S "" `"ylabel(, notick)"'
_axl_probe lab_lab_nolab S "" `"ylabel(, labels nolabels)"'
_axl_probe lab_ticks_noticks S "" `"ylabel(, ticks noticks)"'
_axl_probe lab_noticks_ticks S "" `"ylabel(, noticks ticks)"'
_axl_probe lab_copies_lab_nolab S "" `"ylabel(, labels) ylabel(, nolabels)"'
_axl_probe lab_copies_nolab_lab S "" `"ylabel(, nolabels) ylabel(, labels)"'
_axl_probe lab_labcolor S "" `"ylabel(, labcolor(red))"'
_axl_probe lab_labc_alpha S "" `"ylabel(, labc(red%50))"'
_axl_probe lab_labcolor_bogus S "" `"ylabel(, labcolor(bogus))"'
_axl_probe lab_labcolor_Red S "" `"ylabel(, labcolor(Red))"'
_axl_probe lab_tl3 S "" `"ylabel(, tlength(3))"'
_axl_probe lab_tl0 S "" `"ylabel(, tlength(0))"'
_axl_probe lab_tl_neg S "" `"ylabel(, tlength(-1))"'
_axl_probe lab_tl_neg_inside S "" `"ylabel(, tlength(-1) tposition(inside))"'
_axl_probe lab_tl_star2 S "" `"ylabel(, tlength(*2))"'
_axl_probe lab_tl_bogus S "" `"ylabel(, tlength(bogus))"'
_axl_probe lab_tl_10pt S "" `"ylabel(, tlength(10pt))"'
_axl_probe lab_tp_outside S "" `"ylabel(, tposition(outside))"'
_axl_probe lab_tp_inside S "" `"ylabel(, tposition(inside))"'
_axl_probe lab_tp_crossing S "" `"ylabel(, tposition(crossing))"'
_axl_probe lab_tp_o S "" `"ylabel(, tposition(o))"'
_axl_probe lab_tp_i S "" `"ylabel(, tposition(i))"'
_axl_probe lab_tp_c S "" `"ylabel(, tposition(c))"'
_axl_probe lab_tp_bogus S "" `"ylabel(, tposition(bogus))"'
_axl_probe lab_tp_Inside S "" `"ylabel(, tposition(Inside))"'
_axl_probe lab_quoted S "" `"ylabel(10 "nolabels" 20 "angle(45)" 30)"'
_axl_probe ang_default S "" `"ylabel(, angle(default))"'
_axl_probe ang_zero S "" `"ylabel(, angle(zero))"'
_axl_probe ang_horizontal S "" `"ylabel(, angle(horizontal))"'
_axl_probe ang_forty_five S "" `"ylabel(, angle(forty_five))"'
_axl_probe ang_ninety S "" `"ylabel(, angle(ninety))"'
_axl_probe ang_vertical S "" `"ylabel(, angle(vertical))"'
_axl_probe ang_rhorizontal S "" `"ylabel(, angle(rhorizontal))"'
_axl_probe ang_rvertical S "" `"ylabel(, angle(rvertical))"'
_axl_probe ang_two_seventy S "" `"ylabel(, angle(two_seventy))"'
_axl_probe ang_stdarrow S "" `"ylabel(, angle(stdarrow))"'
_axl_probe ang_h S "" `"ylabel(, angle(h))"'
_axl_probe ang_v S "" `"ylabel(, angle(v))"'
_axl_probe ang_ve S "" `"ylabel(, angle(ve))"'
_axl_probe ang_rh S "" `"ylabel(, angle(rh))"'
_axl_probe ang_rho S "" `"ylabel(, angle(rho))"'
_axl_probe ang_rv S "" `"ylabel(, angle(rv))"'
_axl_probe ang_rve S "" `"ylabel(, angle(rve))"'
_axl_probe ang_r S "" `"ylabel(, angle(r))"'
_axl_probe ang_forty S "" `"ylabel(, angle(forty))"'
_axl_probe ang_Vertical S "" `"ylabel(, angle(Vertical))"'
_axl_probe ang_V S "" `"ylabel(, angle(V))"'
_axl_probe ang_Rv S "" `"ylabel(, angle(Rv))"'
_axl_probe ang_stacked S "" `"ylabel(, angle(stacked))"'
_axl_probe ang_45deg S "" `"ylabel(, angle(45deg))"'
_axl_probe ang_m90 S "" `"ylabel(, angle(-90))"'
_axl_probe ang_m45_5 S "" `"ylabel(, angle(-45.5))"'
_axl_probe ang_1e2 S "" `"ylabel(, angle(1e2))"'
_axl_probe ang_plus30 S "" `"ylabel(, angle(+30))"'
_axl_probe ang_360 S "" `"ylabel(, angle(360))"'
_axl_probe ang_m360 S "" `"ylabel(, angle(-360))"'
_axl_probe ang_stacked_s2 S "s2color" `"ylabel(, angle(stacked))"'
_axl_probe xang_rv S "" `"xlabel(, angle(rv))"'
_axl_probe y2ang_rv Y2 "" `"ylabel(, axis(2) angle(rvertical))"'
_axl_probe sc_off S "" `"yscale(off)"'
_axl_probe sc_off_title S "" `"ytitle("Hi") yscale(off)"'
_axl_probe sc_off_on S "" `"yscale(off on)"'
_axl_probe sc_on_off S "" `"yscale(on off)"'
_axl_probe sc_off_copies_on S "" `"yscale(off) yscale(on)"'
_axl_probe sc_noline S "" `"yscale(noline)"'
_axl_probe sc_noli S "" `"yscale(noli)"'
_axl_probe sc_noline_line S "" `"yscale(noline line)"'
_axl_probe sc_line_noline S "" `"yscale(line noline)"'
_axl_probe sc_noli_lc S "" `"yscale(noli lc(red))"'
_axl_probe sc_lc_noline S "" `"yscale(lc(red) noline)"'
_axl_probe sc_noline_lw S "" `"yscale(noline lwidth(thick))"'
_axl_probe sc_noline_lp S "" `"yscale(noline lpattern(dash))"'
_axl_probe sc_style S "" `"yscale(lcolor(red) lwidth(thick) lpattern(dash))"'
_axl_probe sc_style_abbr S "" `"yscale(lc(red) lw(1) lp(shortdash))"'
_axl_probe sc_lc_bogus S "" `"yscale(lcolor(bogus))"'
_axl_probe sc_lp_bogus S "" `"yscale(lpattern(bogus))"'
_axl_probe sc_lp_Dash S "" `"yscale(lpattern(Dash))"'
_axl_probe sc_lw_bogus S "" `"yscale(lwidth(bogus))"'
_axl_probe sc_lw_star2 S "" `"yscale(lwidth(*2))"'
_axl_probe sc_alt S "" `"yscale(alt)"'
_axl_probe sc_xalt S "" `"xscale(alt)"'
_axl_probe sc_alt_copies S "" `"yscale(alt) yscale(alt)"'
_axl_probe sc_tgap5 S "" `"yscale(titlegap(5))"'
_axl_probe sc_tgap0 S "" `"yscale(titleg(0))"'
_axl_probe sc_tgap_neg S "" `"yscale(titlegap(-2))"'
_axl_probe sc_tgap_star2 S "" `"yscale(titlegap(*2))"'
_axl_probe sc_tgap_bogus S "" `"yscale(titlegap(bogus))"'
_axl_probe econ_alt S "economist" `"yscale(alt)"'
_axl_probe econ_lc S "economist" `"yscale(lcolor(red))"'
_axl_probe econ_line S "economist" `"yscale(line)"'
_axl_probe econ_ticks S "economist" `"ylabel(, ticks)"'
_axl_probe y2_alt1 Y2 "" `"yscale(alt)"'
_axl_probe y2_alt2 Y2 "" `"yscale(alt axis(2))"'
_axl_probe y2_altboth Y2 "" `"yscale(alt) yscale(alt axis(2))"'
_axl_probe y2_off2 Y2 "" `"yscale(off axis(2))"'
_axl_probe y2_nolab2 Y2 "" `"ylabel(, axis(2) nolabels)"'
_axl_probe y2_lc2 Y2 "" `"yscale(lcolor(red) axis(2))"'
_axl_probe y2_tgap2 Y2 "" `"yscale(titlegap(5) axis(2))"'
_axl_probe by_base BY "" `""'
_axl_probe by_off BY "" `"yscale(off)"'
_axl_probe by_xoff BY "" `"xscale(off)"'
_axl_probe by_nolab BY "" `"ylabel(, nolabels)"'
_axl_probe by_noticks BY "" `"ylabel(, noticks)"'
_axl_probe by_tgap BY "" `"yscale(titlegap(10))"'
_axl_probe by_tgap_bogus BY "" `"yscale(titlegap(bogus))"'
_axl_probe by_noline BY "" `"yscale(noline)"'
_axl_probe by_alt BY "" `"yscale(alt)"'
_axl_probe by_xalt BY "" `"xscale(alt)"'
_axl_probe by_lc BY "" `"yscale(lcolor(red))"'
_axl_probe by_labc BY "" `"ylabel(, labcolor(red))"'
_axl_probe by_tl BY "" `"ylabel(, tlength(5))"'
_axl_probe by_tp BY "" `"ylabel(, tposition(inside))"'
_axl_probe by_ang BY "" `"ylabel(, angle(vertical))"'
_axl_probe by_style BY "" `"yscale(lwidth(thick) lpattern(dash))"'
_axl_probe by_ytick_noticks BY "" `"ytick(25, noticks)"'
_axl_probe by_ytick_tl BY "" `"ytick(25, tlength(5))"'
_axl_probe by_y2_base Y2BY "" `""'
_axl_probe by_y2_nolab Y2BY "" `"ylabel(, axis(2) nolabels)"'
_axl_probe by_y2_off Y2BY "" `"yscale(off axis(2))"'
_axl_probe tk_base S "" `"ylabel(10(10)40) ytick(25)"'
_axl_probe tk_lab_noticks S "" `"ylabel(10(10)40, noticks) ytick(25)"'
_axl_probe tk_lab_tl S "" `"ylabel(10(10)40, tlength(5)) ytick(25)"'
_axl_probe tk_own_tl S "" `"ylabel(10(10)40) ytick(25, tlength(5))"'
_axl_probe tk_own_noticks S "" `"ylabel(10(10)40) ytick(25, noticks)"'
_axl_probe tk_own_tp S "" `"ylabel(10(10)40) ytick(25, tposition(inside))"'
_axl_probe rf_ang400 S "" `"ylabel(, angle(400))"'
_axl_probe rf_angm361 S "" `"ylabel(, ang(-361))"'
_axl_probe rf_ang360_5 S "" `"ylabel(, angle(360.5))"'
_axl_probe rf_ang1e3 S "" `"ylabel(, angle(1e3))"'
_axl_probe rf_angplus400 S "" `"ylabel(, angle(+400))"'
_axl_probe rf_xang400 S "" `"xlabel(, angle(400))"'
_axl_probe rf_ytick_ang S "" `"ytick(25, angle(400))"'
_axl_probe rf_ymlabel_ang S "" `"ymlabel(25, angle(400))"'
_axl_probe rf_ymtick_ang S "" `"ymtick(25, angle(400))"'
_axl_probe rf_y2_ang Y2 "" `"ylabel(, axis(2) angle(400))"'
_axl_probe rf_by_ang BY "" `"ylabel(, angle(400))"'
_axl_probe rf_nodraw_ang S "" `"ylabel(, angle(400)) nodraw"'
_axl_probe rf_lw_neg S "" `"yscale(lwidth(-1))"'
_axl_probe rf_lw_abbr S "" `"yscale(lw(-1))"'
_axl_probe rf_lw_big S "" `"yscale(lwidth(20000))"'
_axl_probe rf_y2_lw Y2 "" `"yscale(axis(2) lwidth(-1))"'
_axl_probe rf_by_lw BY "" `"yscale(lwidth(-1))"'
_axl_probe rf_OFF S "" `"yscale(OFF)"'
_axl_probe rf_Alt S "" `"yscale(Alt)"'
_axl_probe rf_ALT S "" `"yscale(ALT)"'
_axl_probe rf_bogus S "" `"xscale(bogus)"'
_axl_probe rf_alt_alt S "" `"yscale(alt alt)"'
_axl_probe rf_lw_dup S "" `"yscale(lwidth(-1) lwidth(1))"'
_axl_probe rf_ord_xlab_yscale S "" `"xlabel(, angle(400)) yscale(lwidth(-1))"'
_axl_probe rf_ord_ylab_xscale S "" `"ylabel(, angle(400)) xscale(lwidth(-1))"'
_axl_probe rf_ord_ylab_yscale S "" `"ylabel(, angle(400)) yscale(lwidth(-1))"'
_axl_probe rf_ord_cap_angle S "" `"ylabel(, angle(400)) yscale(OFF)"'
_axl_probe rf_ord_y1lab_y2scale Y2 "" `"ylabel(, angle(400)) yscale(axis(2) lwidth(-1))"'
_axl_probe rf_ord_y2lab_x1scale Y2 "" `"ylabel(, axis(2) angle(400)) xscale(lwidth(-1))"'
_axl_probe rf_ord_y2lab_x2scale Y2 "" `"ylabel(, axis(2) angle(400)) xscale(axis(2) lwidth(-1))"'
_axl_probe rf_ord_x2lab_y2scale Y2 "" `"xlabel(, axis(2) angle(400)) yscale(axis(2) lwidth(-1))"'
_axl_probe rf_merge_seg_after SEG400 "" `"ylabel(, angle(0))"'
_axl_probe rf_merge_after_seg SEG0 "" `"ylabel(, angle(400))"'
_axl_probe rf_merge_lw SEGLW "" `"yscale(lw(1))"'
_axl_probe rf_comma_labc S "" `"ylabel(, labcolor("255,0,0"))"'
file close axlrec

python:
import json, os, re, sys
from sfi import Macro

REPO = Macro.getGlobal("AXL_REPO")
WORK = Macro.getGlobal("AXL_WORK")
sys.path.insert(0, os.path.join(REPO, "scripts"))
import svg_truth

KEYS = ("draw_view", "show_labels", "show_ticks", "length", "position",
        "label_color", "tickangle", "line_color", "line_width",
        "line_pattern", "axis_position", "title_gap")
MSG = ("option", "textangle", "gm_linewidth", "invalid", "(note:")

probes, order, stems = {}, [], {}
with open(Macro.getGlobal("AXL_REC"), encoding="utf-8", errors="replace") as fh:
    for line in fh:
        f = line.rstrip("\n").split("|")
        if f[0] == "P":
            pid = f[1]
            stems[pid] = f[4]
            probes[pid] = {"cmd": "|".join(f[5:]), "scheme": f[3] or "stcolor",
                           "rc": int(f[2]), "messages": [], "members": {},
                           "svg": None}
            order.append(pid)
        elif f[0] == "M" and f[1] in probes:
            vals = (f[3:] + [""] * len(KEYS))[:len(KEYS)]
            probes[f[1]]["members"][f[2]] = dict(zip(KEYS, vals))


def messages(path):
    """The log's lines that start a message (the command is run inside a
    program, so the log holds its output only)."""
    out = []
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return out
    full = []
    for ln in lines:
        if ln.startswith("> ") and full:
            full[-1] += ln[2:]
        else:
            full.append(ln)
    for ln in full:
        s = ln.strip()
        if s.startswith(MSG):
            out.append(s)
    return out


for pid in order:
    p = probes[pid]
    p["messages"] = messages(os.path.join(WORK, stems[pid] + ".log"))
    svg = os.path.join(WORK, stems[pid] + ".svg")
    if p["rc"] == 0 and os.path.exists(svg):
        d = svg_truth.svg_document(svg)
        def short(L):
            # The ticks: short lines, less the dashes of a dashed grid
            # (one length and colour more than 20 times).
            rows = [[round(l["x1"]), round(l["x2"]), round(l["y1"]),
                     round(l["y2"]), l["stroke"], l["width"], l["dasharray"]]
                    for l in L
                    if abs(l["x2"] - l["x1"]) + abs(l["y2"] - l["y1"]) < 200]
            seen = {}
            for r in rows:
                k = (abs(r[1] - r[0]) + abs(r[3] - r[2]), r[4])
                seen[k] = seen.get(k, 0) + 1
            return [r for r in rows
                    if seen[(abs(r[1] - r[0]) + abs(r[3] - r[2]), r[4])] <= 20]
        p["svg"] = {
            "texts": [[t["text"], round(t["x"] or 0), round(t["y"] or 0),
                       t["fill"], t["rotate"]] for t in d["texts"]],
            "hticks": short(d["hlines"]), "vticks": short(d["vlines"]),
            # The long lines: the axis lines and gridlines.
            "lines": [[round(l["x1"]), round(l["x2"]), round(l["y1"]),
                       round(l["y2"]), l["stroke"], l["width"],
                       l["dasharray"]] for l in d["hlines"] + d["vlines"]
                      if abs(l["x2"] - l["x1"]) + abs(l["y2"] - l["y1"]) >= 200],
            "plotregion": d["plotregion"]}

meta = {"stata_version": Macro.getGlobal("AXL_META_VERSION"),
        "born_date": Macro.getGlobal("AXL_META_BORN"),
        "dash_commit": Macro.getGlobal("AXL_META_COMMIT"),
        "extracted": Macro.getGlobal("AXL_META_DATE"),
        "scheme_in_force": Macro.getGlobal("AXL_META_SCHEME")}
out = os.path.join(REPO, "test", "fixtures", "axis_subopt_truth.json")
with open(out, "w", encoding="utf-8") as fh:
    json.dump({"_meta": meta, "probes": {k: probes[k] for k in order}}, fh,
              separators=(",", ":"))
    fh.write("\n")
print("axis_subopt_truth.json: %d probes" % len(order))
end
