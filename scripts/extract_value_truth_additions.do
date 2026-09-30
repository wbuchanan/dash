*! scripts/extract_value_truth_additions.do: measure twoway's verdict on option
*! values for rules added to dash.ado's _dash_option_rules after the original
*! test/fixtures/value_truth.json run.  One log per probe (probe_<id>.log,
*! probe_<id>.rc: rc, option, value,
*! command) in the working directory; scripts/merge_value_truth.py
*! reads them into the fixture.  Run via scripts/stata_slot.sh <dir> <file>.
version 19
set more off
set graphics off
sysuse auto, clear
capture log close _all

program define _vt_probe
    args id option value cmd
    quietly log using `"probe_`id'.log"', text replace name(vt)
    capture noisily `cmd'
    local rc = _rc
    quietly log close vt
    file open fh using `"probe_`id'.rc"', write text replace
    file write fh "`rc'" _n
    file write fh `"`option'"' _n `"`value'"' _n `"`cmd'"' _n
    file close fh
end

* colorlevels (twoway scatter's colorvar() sub-option)
local i = 0
foreach v in abc 1 2 4 256 257 -1 2.5 {
    local ++i
    _vt_probe colorlevels_`i' colorlevels `"`v'"' `"twoway scatter mpg weight, colorvar(price) colorlevels(`v')"'
}
* axis-label and tick options (the second axis created with xaxis/yaxis(1 2))
foreach o in ylabel xlabel2 ylabel2 xtick ytick xmtick ymtick xmlabel ymlabel {
    local isx = substr("`o'", 1, 1) == "x"
    local lo = cond(`isx', "1000(1000)5000", "10(5)40")
    local ax2 = ""
    if substr("`o'", -1, 1) == "2" {
        local ax2 = cond(`isx', "xaxis(1 2)", "yaxis(1 2)")
    }
    _vt_probe `o'_1 `o' abc `"twoway scatter mpg weight, `ax2' `o'(abc)"'
    _vt_probe `o'_2 `o' #5 `"twoway scatter mpg weight, `ax2' `o'(#5)"'
    _vt_probe `o'_3 `o' `"`lo'"' `"twoway scatter mpg weight, `ax2' `o'(`lo')"'
}
