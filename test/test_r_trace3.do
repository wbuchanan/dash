sysuse auto, clear
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash/"
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON/"

// Load mata (suppressing already-defined errors)
capture {
    do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"
}
// Load ado (programs auto-loaded from adopath)
// Test _dash_parse_varpart_std via dash clear (loads dash.ado)
dash clear

// Now test the critical path
_dash_parse_varpart_std mpg weight if rep78==1
display `"varlist: `s(varlist)'"'
display `"if_clause: `s(if_clause)'"'

local if_cl `"`s(if_clause)'"'
local if_expr = strtrim(substr(`"`if_cl'"', 5, .))
display `"if_expr after strtrim/substr: `if_expr'"'

// Check _dash_json_str
_dash_json_str "`if_expr'" _jif
display `"_jif: `_jif'"'

// Check the seg_json assembly
local ptype "scatter"
local _jyv "mpg"
local _jxv "weight"
local _opts_json `"{"mcolor":"navy","msymbol":"circle","msize":"small"}"'
local _jin ""
local vfields `""yvar":"mpg","xvar":"weight""'

local seg_json `"{"type":"`ptype'",`vfields',"options":`_opts_json',"if_expr":"`_jif'","in_expr":"`_jin'"}"'

tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"`seg_json'"'
file close `fh'
display "seg_json:"
type "`tf'"
