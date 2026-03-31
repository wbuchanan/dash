// Trace where 'r' disappears in if_expr handling
sysuse auto, clear
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"

dash clear

// Register s1 manually tracing through _dash_plot steps
// Step 1: parse segment
local seg = "scatter mpg weight if rep78==1, mc(navy) ms(circle) msi(small)"

// Extract plottype
gettoken plottype rest : seg
mata: _dash_expand_plottype(strlower("`plottype'"), "_pt_exp")
local ptype "`_pt_exp'"
display "ptype: `ptype'"

// Find comma
local comma_pos = 0
mata: _dash_comma_pos(`"`rest'"', "comma_pos")
local varpart  = strtrim(substr(`"`rest'"', 1, `comma_pos' - 1))
local opts_raw = strtrim(substr(`"`rest'"', `comma_pos' + 1, .))
display `"varpart: `varpart'"'
display `"opts_raw: `opts_raw'"'

// Parse varpart  
_dash_parse_varpart_std `varpart'
local vl = "`s(varlist)'"
local yvar = word("`vl'", 1)
local xvar = word("`vl'", 2)
local if_cl `"`s(if_clause)'"'
display `"if_cl: `if_cl'"'

// Extract if_expr
local if_expr ""
if `"`if_cl'"' != "" {
    local if_expr = strtrim(substr(`"`if_cl'"', 5, .))
}
display `"if_expr (raw): `if_expr'"'

// JSON str escape
_dash_json_str "`if_expr'" _jif
display `"_jif after _dash_json_str: `_jif'"'

// Full seg_json
local opts_exp ""
mata: _dash_expand_opts_str(`"`opts_raw'"', "opts_exp")
sreturn clear
_dash_parse_plot_opts , `opts_exp'
_dash_plot_opts_to_json _opts_json
display `"_opts_json: `_opts_json'"'

_dash_json_str "`yvar'" _jyv
_dash_json_str "`xvar'" _jxv
local vfields `""yvar":"`_jyv'","xvar":"`_jxv'""'
local _jin ""

local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'

// Write to file
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"`seg_json'"'
file close `fh'
display "seg_json:"
type "`tf'"
