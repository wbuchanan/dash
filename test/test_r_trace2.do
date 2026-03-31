sysuse auto, clear
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"

// Test _dash_parse_varpart_std directly
_dash_parse_varpart_std mpg weight if rep78==1
display `"varlist: `s(varlist)'"'
display `"if_clause: `s(if_clause)'"'

local if_cl `"`s(if_clause)'"'
local if_expr = strtrim(substr(`"`if_cl'"', 5, .))
display `"if_expr: `if_expr'"'

// Now test _dash_json_str
_dash_json_str "`if_expr'" _jif
display `"_jif: `_jif'"'
