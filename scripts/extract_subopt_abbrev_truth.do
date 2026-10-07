*! extract_subopt_abbrev_truth.do
*! WP-30 section 10 (P1.19): twoway's reading of sub-option abbreviations
*! for test/fixtures/subopt_abbrev_truth.json.
*!
*! Each probe runs one twoway command (capture noisily, its own log), keeps
*! its return code and the lines twoway printed -- "option ... not allowed",
*! "... invalid -- ...", "(note: ...)" -- and, when it drew, exports the SVG,
*! read through scripts/svg_truth.py (S02) for its texts and lines.  The
*! fixture is never patched by hand: run this again when Stata changes.
*!
*! Run (never the GUI):
*!   DASH_REPO=<repo> <repo>/scripts/stata_slot.sh <scratch> <repo>/scripts/extract_subopt_abbrev_truth.do
*!
*! The trailing python: block never calls Stata, never uses a shell, and
*! holds no backtick.

version 19
clear all
set more off
set linesize 255

* Root (WP-30 P1.34): DASH_REPO, else the current directory when it is a
* dash tree; never another checkout.
local repo : environment DASH_REPO
if `"`macval(repo)'"' == "" local repo `"`c(pwd)'"'
mata: st_local("_zr_bad", strofreal(any(strpos(st_local("repo"), (char(34), char(36), char(39), char(96), char(10), char(13))))))
if `_zr_bad' {
    display as error "extract_subopt_abbrev_truth.do: DASH_REPO may not hold a double quote, dollar sign, single quote, backtick or line break"
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
    display as error `"extract_subopt_abbrev_truth.do: `_zr_show' is not a dash tree; set DASH_REPO to the repository root"'
    exit 601
}
global dash_nobrowser 1
set scheme stcolor
sysuse auto, clear

global ZS_REPO "`repo'"
global ZS_SVER = c(stata_version)
global ZS_BORN = c(born_date)
global ZS_DATE = c(current_date)
global ZS_SCHEME = c(scheme)
tempfile zsgit
quietly shell git -C "${ZS_REPO}" rev-parse HEAD > "`zsgit'"
tempname zsfh
file open `zsfh' using "`zsgit'", read text
file read `zsfh' zsline
file close `zsfh'
global ZS_COMMIT = trim(`"`zsline'"')
tempfile zsbase
global ZS_WORK "`zsbase'_zs"
capture mkdir "${ZS_WORK}"
global ZS_IDS ""
global ZS_N = 0

capture program drop _zs
program define _zs
    version 19
    args id cmd
    // Files are numbered, not named by id: l_SIZE and l_size are one file
    // name on a case-insensitive file system.
    global ZS_N = ${ZS_N} + 1
    local lg "${ZS_WORK}/p${ZS_N}.log"
    local svg "${ZS_WORK}/p${ZS_N}.svg"
    capture erase "`lg'"
    capture erase "`svg'"
    capture graph drop zs
    quietly log using "`lg'", text replace name(_zs)
    capture noisily `cmd' name(zs, replace)
    local rc = _rc
    quietly log close _zs
    if `rc' == 0 quietly graph export "`svg'", replace name(zs)
    capture graph drop zs
    global ZS_RC_`id' = `rc'
    global ZS_F_`id' "p${ZS_N}"
    global ZS_CMD_`id' `"`cmd'"'
    global ZS_IDS "${ZS_IDS} `id'"
    display as text "probe `id' rc=`rc'"
end

_zs l_base `"twoway (scatter mpg weight) (lfit mpg weight),"'
_zs l_cols2 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(2))"'
_zs l_c2 `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(2))"'
_zs l_co2 `"twoway (scatter mpg weight) (lfit mpg weight), legend(co(2))"'
_zs l_col2 `"twoway (scatter mpg weight) (lfit mpg weight), legend(col(2))"'
_zs l_rows1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(rows(1))"'
_zs l_r1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(r(1))"'
_zs l_r1_k3 `"twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight), legend(r(1))"'
_zs l_label `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1 "XX"))"'
_zs l_lab `"twoway (scatter mpg weight) (lfit mpg weight), legend(lab(1 "XX"))"'
_zs l_labe `"twoway (scatter mpg weight) (lfit mpg weight), legend(labe(1 "XX"))"'
_zs l_la `"twoway (scatter mpg weight) (lfit mpg weight), legend(la(1 "XX"))"'
_zs l_position9 `"twoway (scatter mpg weight) (lfit mpg weight), legend(position(9))"'
_zs l_pos9 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(9))"'
_zs l_posi9 `"twoway (scatter mpg weight) (lfit mpg weight), legend(posi(9))"'
_zs l_pos_sp `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos( 9 ))"'
_zs l_size `"twoway (scatter mpg weight) (lfit mpg weight), legend(size(large))"'
_zs l_si `"twoway (scatter mpg weight) (lfit mpg weight), legend(si(large))"'
_zs l_s `"twoway (scatter mpg weight) (lfit mpg weight), legend(s(large))"'
_zs l_siz `"twoway (scatter mpg weight) (lfit mpg weight), legend(siz(large))"'
_zs l_lastlabel `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlabel(1 "XX"))"'
_zs l_lastlab `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlab(1 "XX"))"'
_zs l_lastlabe `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlabe(1 "XX"))"'
_zs l_color_red `"twoway (scatter mpg weight) (lfit mpg weight), legend(color(red))"'
_zs l_colo_red `"twoway (scatter mpg weight) (lfit mpg weight), legend(colo(red))"'
_zs l_fall_c `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1) c(red))"'
_zs l_fall_cc `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(1) c(red))"'
_zs l_fall_c3 `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(1) c(2))"'
_zs l_fall_sty `"twoway (scatter mpg weight) (lfit mpg weight), legend(style(foreground) sty(foreground))"'
_zs l_rep_region `"twoway (scatter mpg weight) (lfit mpg weight), legend(region(fcolor(red)) reg(lcolor(blue)))"'
_zs l_rep_title `"twoway (scatter mpg weight) (lfit mpg weight), legend(title("TA") title("TB"))"'
_zs l_rep_label `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1 "AA") lab(1 "BB"))"'
_zs l_t_title `"twoway (scatter mpg weight) (lfit mpg weight), legend(t("TT"))"'
_zs l_l_title `"twoway (scatter mpg weight) (lfit mpg weight), legend(l("TT"))"'
_zs l_b_title `"twoway (scatter mpg weight) (lfit mpg weight), legend(b("TT"))"'
_zs l_po9 `"twoway (scatter mpg weight) (lfit mpg weight), legend(po(9))"'
_zs l_rin0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(rin(0) pos(5))"'
_zs l_ord `"twoway (scatter mpg weight) (lfit mpg weight), legend(ord(2 1))"'
_zs l_o `"twoway (scatter mpg weight) (lfit mpg weight), legend(o(2 1))"'
_zs l_lastl `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastl(1 "XX"))"'
_zs l_of `"twoway (scatter mpg weight) (lfit mpg weight), legend(of)"'
_zs l_OFF `"twoway (scatter mpg weight) (lfit mpg weight), legend(OFF)"'
_zs l_POS `"twoway (scatter mpg weight) (lfit mpg weight), legend(POS(9))"'
_zs l_Pos `"twoway (scatter mpg weight) (lfit mpg weight), legend(Pos(9))"'
_zs l_SIZE `"twoway (scatter mpg weight) (lfit mpg weight), legend(SIZE(large))"'
_zs l_Cols `"twoway (scatter mpg weight) (lfit mpg weight), legend(Cols(1))"'
_zs l_c_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(2) cols(1))"'
_zs l_pos_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(9) position(6))"'
_zs l_size_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(size(large) size(small))"'
_zs l_s_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(size(large) s(small))"'
_zs l_order_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(1 2) order(2 1))"'
_zs l_on_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(on on)"'
_zs l_holes_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes(1) holes(2))"'
_zs l_rows_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(rows(1) r(2))"'
_zs l_ring_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(ring(0) pos(5) ring(1))"'
_zs l_c3_dup `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(2) c(3) c(4))"'
_zs l_cols_word `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols)"'
_zs l_on_arg `"twoway (scatter mpg weight) (lfit mpg weight), legend(on(1))"'
_zs l_garbage `"twoway (scatter mpg weight) (lfit mpg weight), legend(garbage)"'
_zs l_c_red `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(red))"'
_zs l_cols0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(0))"'
_zs l_cols_neg `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(-1))"'
_zs l_cols15 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1.5))"'
_zs l_cols05 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(0.5))"'
_zs l_cols12 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1 2))"'
_zs l_cols13 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1/3))"'
_zs l_cols113 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1(1)3))"'
_zs l_colsdot `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(.))"'
_zs l_colsdota `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(.a))"'
_zs l_cols_big `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1e400))"'
_zs l_cols22 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(2/2))"'
_zs l_cols_empty `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols())"'
_zs l_cols_plus `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(+2))"'
_zs l_cols_1x `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(1 x))"'
_zs l_cols_x1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(x 1))"'
_zs l_rows_x `"twoway (scatter mpg weight) (lfit mpg weight), legend(rows(x))"'
_zs l_r0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(r(0))"'
_zs l_holes0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes(0))"'
_zs l_holes15 `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes(1.5))"'
_zs l_holes301 `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes(1/301))"'
_zs l_holes_empty `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes())"'
_zs l_xoff_x `"twoway (scatter mpg weight) (lfit mpg weight), legend(xoffset(x))"'
_zs l_xoff_empty `"twoway (scatter mpg weight) (lfit mpg weight), legend(xoffset())"'
_zs l_yoff12 `"twoway (scatter mpg weight) (lfit mpg weight), legend(yoffset(1 2))"'
_zs l_label_x `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(x "A"))"'
_zs l_label_15 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1.5 "A"))"'
_zs l_label_q `"twoway (scatter mpg weight) (lfit mpg weight), legend(label("A"))"'
_zs l_label_1e0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1e0 "A"))"'
_zs l_label_1x `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1x "A"))"'
_zs l_label_0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(0 "A"))"'
_zs l_label_m1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(-1 "A"))"'
_zs l_lastl_0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlabel(0 "A"))"'
_zs l_lastl_x `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlab(x "A"))"'
_zs l_lastl_q `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlabel("A"))"'
_zs l_label_01 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(01 "A"))"'
_zs l_label_plus `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(+1 "A"))"'
_zs l_label_empty `"twoway (scatter mpg weight) (lfit mpg weight), legend(label())"'
_zs l_label_1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(1))"'
_zs l_posx `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(x))"'
_zs l_pos13 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(13))"'
_zs l_posm1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(-1))"'
_zs l_pos06 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(06))"'
_zs l_pos30 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(3.0))"'
_zs l_ringx `"twoway (scatter mpg weight) (lfit mpg weight), legend(ring(x))"'
_zs l_ringm1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(ring(-1))"'
_zs l_ring15 `"twoway (scatter mpg weight) (lfit mpg weight), legend(ring(1.5))"'
_zs l_orderx `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(x))"'
_zs l_order1x `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(1 x))"'
_zs l_orderx1 `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(x 1))"'
_zs l_order1ax `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(1 "a" x))"'
_zs l_order1e0 `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(1e0))"'
_zs l_order_plus `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(+1 2))"'
_zs l_order_neg `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(-2 1))"'
_zs l_onoff1 `"twoway scatter mpg weight, legend(on off)"'
_zs l_offon1 `"twoway scatter mpg weight, legend(off on)"'
_zs l_onoff2 `"twoway (scatter mpg weight) (lfit mpg weight), legend(on off)"'
_zs m_posx_pos3 `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(x)) legend(pos(3))"'
_zs m_orderx_21 `"twoway (scatter mpg weight) (lfit mpg weight), legend(order(x)) legend(order(2 1))"'
_zs m_on_off `"twoway (scatter mpg weight) (lfit mpg weight), legend(on) legend(off)"'
_zs m_off_on1 `"twoway scatter mpg weight, legend(off) legend(on)"'
_zs m_cc `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(2)) legend(cols(1))"'
_zs m_lab_ab `"twoway (scatter mpg weight) (lfit mpg weight), legend(lab(1 "AA")) legend(lab(2 "BB"))"'
_zs m_lab_same `"twoway (scatter mpg weight) (lfit mpg weight), legend(lab(1 "AA")) legend(lab(1 "BB"))"'
_zs m_t_s `"twoway scatter mpg weight, title("A", s(large)) title(, size(small))"'
_zs m_sc_union `"twoway scatter mpg weight, xscale(r(1000 3000)) xscale(range(2000 6000))"'
_zs k_rowscols `"twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight), legend(cols(3) rows(1))"'
_zs k_colsrows `"twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight), legend(rows(1) cols(2))"'
_zs k_cr `"twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight), legend(cols(1)) legend(rows(1))"'
_zs k_rc `"twoway (scatter mpg weight) (lfit mpg weight) (scatter price weight), legend(rows(1)) legend(cols(1))"'
_zs a_base `"twoway scatter mpg weight,"'
_zs a_labsize `"twoway scatter mpg weight, ylabel(, labsize(large))"'
_zs a_labs `"twoway scatter mpg weight, ylabel(, labs(large))"'
_zs a_labsi `"twoway scatter mpg weight, ylabel(, labsi(large))"'
_zs a_angle `"twoway scatter mpg weight, ylabel(, angle(0))"'
_zs a_ang `"twoway scatter mpg weight, ylabel(, ang(0))"'
_zs a_format `"twoway scatter mpg weight, ylabel(, format(%9.1f))"'
_zs a_form `"twoway scatter mpg weight, ylabel(, form(%9.1f))"'
_zs a_for `"twoway scatter mpg weight, ylabel(, for(%9.1f))"'
_zs a_nogrid `"twoway scatter mpg weight, ylabel(, nogrid)"'
_zs a_nogr `"twoway scatter mpg weight, ylabel(, nogr)"'
_zs a_nog `"twoway scatter mpg weight, ylabel(, nog)"'
_zs g_grid `"twoway scatter mpg weight, scheme(s2color) ylabel(, grid)"'
_zs g_gr `"twoway scatter mpg weight, scheme(s2color) ylabel(, gr)"'
_zs g_g `"twoway scatter mpg weight, scheme(s2color) ylabel(, g)"'
_zs g_gri `"twoway scatter mpg weight, scheme(s2color) ylabel(, gri)"'
_zs a_glcolor `"twoway scatter mpg weight, ylabel(, glcolor(red))"'
_zs a_glc `"twoway scatter mpg weight, ylabel(, glc(red))"'
_zs a_labc `"twoway scatter mpg weight, ylabel(, labc(red))"'
_zs a_nolab `"twoway scatter mpg weight, ylabel(, nolab)"'
_zs a_notick `"twoway scatter mpg weight, ylabel(, notick)"'
_zs f_val `"twoway scatter mpg foreign, xlabel(0 1, val)"'
_zs f_valuelabel `"twoway scatter mpg foreign, xlabel(0 1, valuelabel)"'
_zs f_valuelabels `"twoway scatter mpg foreign, xlabel(0 1, valuelabels)"'
_zs a_lab_s `"twoway scatter mpg weight, ylabel(, lab(large))"'
_zs a_LABS `"twoway scatter mpg weight, ylabel(, LABS(large))"'
_zs a_LABSize `"twoway scatter mpg weight, ylabel(, LABSize(large))"'
_zs a_a `"twoway scatter mpg weight, ylabel(, a(0))"'
_zs a_an `"twoway scatter mpg weight, ylabel(, an(45))"'
_zs a_f `"twoway scatter mpg weight, ylabel(, f(%9.1f))"'
_zs a_fo `"twoway scatter mpg weight, ylabel(, fo(%9.1f))"'
_zs a_gl `"twoway scatter mpg weight, ylabel(, gl(red))"'
_zs a_nola `"twoway scatter mpg weight, ylabel(, nola)"'
_zs a_no `"twoway scatter mpg weight, ylabel(, no)"'
_zs f_va `"twoway scatter mpg foreign, xlabel(0 1, va)"'
_zs a_labs_word `"twoway scatter mpg weight, ylabel(, labs)"'
_zs a_labsize_word `"twoway scatter mpg weight, ylabel(, labsize)"'
_zs a_nog_arg `"twoway scatter mpg weight, ylabel(, nog(1))"'
_zs a_nogrid_arg `"twoway scatter mpg weight, ylabel(, nogrid(1))"'
_zs a_dupang `"twoway scatter mpg weight, ylabel(, angle(45) ang(0))"'
_zs a_duplabs `"twoway scatter mpg weight, ylabel(, labsize(large) labsize(small))"'
_zs a_dupfor `"twoway scatter mpg weight, ylabel(, format(%9.1f) for(%9.2f))"'
_zs a_dupglc `"twoway scatter mpg weight, ylabel(, glc(red) glcolor(blue))"'
_zs a_bogus `"twoway scatter mpg weight, ylabel(, labs(large) bogus)"'
_zs a_bogus2 `"twoway scatter mpg weight, ylabel(, bogus labs(large) labs(small))"'
_zs a_labs_labsword `"twoway scatter mpg weight, ylabel(, labs(large) labs)"'
_zs a_labsword_labs `"twoway scatter mpg weight, ylabel(, labs labs(large))"'
_zs a_labs_LABSIZE `"twoway scatter mpg weight, ylabel(, labs(large) LABSIZE(small))"'
_zs a_dup_word `"twoway scatter mpg weight, ylabel(, nogr nogrid)"'
_zs a_grid_nogrid `"twoway scatter mpg weight, ylabel(, grid nogrid)"'
_zs a_nogrid_grid `"twoway scatter mpg weight, ylabel(, nogrid grid)"'
_zs a_val_noval `"twoway scatter mpg foreign, xlabel(0 1, valuelabel novaluelabel)"'
_zs a_lml_x `"twoway scatter mpg weight, ylabel(, labelminlen(x))"'
_zs a_lml_15 `"twoway scatter mpg weight, ylabel(, labelminlen(1.5))"'
_zs a_lml_empty `"twoway scatter mpg weight, ylabel(, labelminlen())"'
_zs a_tick_labs `"twoway scatter mpg weight, ytick(, labs(large))"'
_zs a_tick_a `"twoway scatter mpg weight, ytick(, a(45))"'
_zs a_mlabel_a `"twoway scatter mpg weight, ymlabel(, a(45))"'
_zs z_a `"twoway scatter mpg weight, colorvar(price) zlabel(, a(45))"'
_zs z_labs `"twoway scatter mpg weight, colorvar(price) zlabel(, labs(large))"'
_zs z_dup `"twoway scatter mpg weight, colorvar(price) zlabel(, labs(large) labs(small))"'
_zs n_quoted `"twoway scatter mpg weight, ylabel(10 "labsize(large)" 20)"'
_zs n_nocomma `"twoway scatter mpg weight, ylabel(10 20)"'
_zs o_leg_ax `"twoway (scatter mpg weight) (lfit mpg weight), legend(po(9)) ylabel(, a(45))"'
_zs o_ax_leg `"twoway (scatter mpg weight) (lfit mpg weight), ylabel(, a(45)) legend(po(9))"'
_zs o_leg_axis3 `"twoway (scatter mpg weight) (lfit mpg weight), legend(po(9)) ylabel(, axis(3))"'
_zs o_x_y3 `"twoway scatter mpg weight, xlabel(, a(45)) ylabel(, axis(3))"'
_zs o_axis3_a `"twoway scatter mpg weight, ylabel(, axis(3) a(45))"'
_zs o_lab_tick `"twoway scatter mpg weight, ytick(, a(45)) ylabel(, f(1))"'
_zs o_tick_lab `"twoway scatter mpg weight, ylabel(, f(1)) ytick(, a(45))"'
_zs o_mlab_tick `"twoway scatter mpg weight, ymlabel(, a(45)) ytick(, f(1))"'
_zs o_ylab_xtick `"twoway scatter mpg weight, ylabel(, f(1)) xtick(, a(45))"'
_zs o_z_y `"twoway scatter mpg weight, colorvar(price) zlabel(, a(45)) ylabel(, f(1))"'
_zs o_y_z `"twoway scatter mpg weight, colorvar(price) ylabel(, f(1)) zlabel(, a(45))"'
_zs o_z_line `"twoway scatter mpg weight, colorvar(price) zlabel(, a(45)) xline(3000, l(red))"'
_zs o_z_leg `"twoway scatter mpg weight, colorvar(price) zlabel(, a(45)) legend(po(9))"'
_zs o_c_po `"twoway (scatter mpg weight) (lfit mpg weight), legend(c(red) po(9))"'
_zs o_triple `"twoway (scatter mpg weight) (lfit mpg weight), legend(pos(9) position(6) c(red))"'
_zs o_po_label `"twoway (scatter mpg weight) (lfit mpg weight), legend(po(9) label(x "A"))"'
_zs o_label_cols `"twoway (scatter mpg weight) (lfit mpg weight), legend(label(x "A") cols(red))"'
_zs o_copies `"twoway (scatter mpg weight) (lfit mpg weight), legend(rows(x)) legend(cols(y))"'
_zs o_rows_cols `"twoway (scatter mpg weight) (lfit mpg weight), legend(cols(x) rows(y))"'
_zs o_cols_rows_one `"twoway (scatter mpg weight) (lfit mpg weight), legend(rows(y) cols(x))"'
_zs o_holes_cols `"twoway (scatter mpg weight) (lfit mpg weight), legend(holes(x) cols(y))"'
_zs o_lastl_label `"twoway (scatter mpg weight) (lfit mpg weight), legend(lastlabel(y "b") label(x "a"))"'
_zs o_ax_c `"twoway (scatter mpg weight) (lfit mpg weight), legend(po(9)) legend(c(red))"'
_zs x_base `"twoway scatter mpg weight, xline(3000)"'
_zs x_full `"twoway scatter mpg weight, xline(3000, lcolor(red) lpattern(dash) lwidth(thick))"'
_zs x_abbr `"twoway scatter mpg weight, xline(3000, lc(red) lp(dash) lw(thick))"'
_zs x_lcol `"twoway scatter mpg weight, xline(3000, lcol(red))"'
_zs x_lpatte `"twoway scatter mpg weight, xline(3000, lpatte(dash))"'
_zs x_lwid `"twoway scatter mpg weight, xline(3000, lwid(thick))"'
_zs x_l `"twoway scatter mpg weight, xline(3000, l(red))"'
_zs x_c `"twoway scatter mpg weight, xline(3000, c(red))"'
_zs x_color `"twoway scatter mpg weight, xline(3000, color(red))"'
_zs x_ls `"twoway scatter mpg weight, xline(3000, ls(foreground))"'
_zs x_LC `"twoway scatter mpg weight, xline(3000, LC(red))"'
_zs x_rep `"twoway scatter mpg weight, xline(3000, lc(red)) xline(4000, lcolor(blue))"'
_zs y_abbr `"twoway scatter mpg weight, yline(20, lc(red) lp(dash) lw(thick))"'
_zs t_base `"twoway scatter mpg weight, title("TT")"'
_zs t_size `"twoway scatter mpg weight, title("TT", size(small))"'
_zs t_s `"twoway scatter mpg weight, title("TT", s(small))"'
_zs t_ytitle_s `"twoway scatter mpg weight, ytitle("YY", s(small))"'
_zs t_ls `"twoway scatter mpg weight, title("TT", ls(foreground))"'
_zs t_nob `"twoway scatter mpg weight, title("TT", nob)"'
_zs t_a `"twoway scatter mpg weight, title("TT", a(top))"'
_zs t_b `"twoway scatter mpg weight, title("TT", b)"'
_zs t_SIZE `"twoway scatter mpg weight, title("TT", SIZE(small))"'
_zs t_dup `"twoway scatter mpg weight, title("TT", size(small) s(large))"'
_zs t_style `"twoway scatter mpg weight, title("TT", style(foreground))"'
_zs t_ytitle_SIZE `"twoway scatter mpg weight, ytitle(, SIZE(small))"'
_zs t_ytitle_ls `"twoway scatter mpg weight, ytitle(, ls(x))"'
_zs t_ytitle_dup `"twoway scatter mpg weight, ytitle(, size(small) s(large))"'
_zs t_ytitle_pfx_sfx `"twoway scatter mpg weight, ytitle("Y", prefix suffix)"'
_zs t_note_SIZE `"twoway scatter mpg weight, note("N", SIZE(small))"'
_zs t_rep_SIZE `"twoway scatter mpg weight, title("A") title(, SIZE(small))"'

python:
import json
import os
import re
import sys
from sfi import Macro
repo = Macro.getGlobal("ZS_REPO")
sys.path.insert(0, os.path.join(repo, "scripts"))
import svg_truth
work = Macro.getGlobal("ZS_WORK")
keep = re.compile(r"^(option |options |\(note:)|\(\) invalid --| not an integer| invalid name|does not exist")
probes = {}
for pid in Macro.getGlobal("ZS_IDS").split():
    rc = int(Macro.getGlobal("ZS_RC_" + pid))
    msgs = []
    stem = Macro.getGlobal("ZS_F_" + pid)
    with open(os.path.join(work, stem + ".log"), encoding="utf-8", errors="replace") as fh:
        for line in fh.read().splitlines():
            s = line.strip()
            if s and keep.search(s):
                msgs.append(s)
    rec = {"cmd": Macro.getGlobal("ZS_CMD_" + pid), "rc": rc, "messages": msgs,
           "texts": [], "hlines": [], "vlines": []}
    svg = os.path.join(work, stem + ".svg")
    if rc == 0 and os.path.exists(svg):
        doc = svg_truth.svg_document(svg)
        rec["texts"] = [[t.get("text"), round(t.get("x") or 0), round(t.get("y") or 0),
                         t.get("size"), t.get("fill"), t.get("rotate")]
                        for t in doc.get("texts", [])]
        for key in ("hlines", "vlines"):
            agg = {}
            for ln in doc.get(key, []):
                k = (ln.get("stroke"), ln.get("width"), str(ln.get("dasharray")))
                agg[k] = agg.get(k, 0) + 1
            rec[key] = sorted([list(k) + [n] for k, n in agg.items()], key=str)
    probes[pid] = rec
out = {"_meta": {"stata_version": Macro.getGlobal("ZS_SVER"),
                 "born_date": Macro.getGlobal("ZS_BORN"),
                 "dash_commit": Macro.getGlobal("ZS_COMMIT"),
                 "extracted": Macro.getGlobal("ZS_DATE"),
                 "scheme_in_force": Macro.getGlobal("ZS_SCHEME"),
                 "method": ("each probe's twoway command run with capture noisily into its own "
                            "log (rc and the option/invalid/note lines) and, when it drew, its "
                            "SVG export read through scripts/svg_truth.py, by "
                            "scripts/extract_subopt_abbrev_truth.do")},
       "probes": probes}
path = os.path.join(repo, "test", "fixtures", "subopt_abbrev_truth.json")
with open(path, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=1, sort_keys=True, ensure_ascii=True)
    fh.write("\n")
print("wrote %s: %d probes" % (path, len(probes)))
end
