sysuse auto, clear
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado"

// Test _dash_parse_varpart_std with if rep78==1
_dash_parse_varpart_std mpg weight if rep78==1
display `"varlist: `s(varlist)'"'
display `"if_clause: `s(if_clause)'"'

local if_cl `"`s(if_clause)'"'
display `"if_cl length: " strlen(`"`if_cl'"')'
display `"if_cl first 5 chars: " substr(`"`if_cl'"',1,5)'

local if_expr = strtrim(substr(`"`if_cl'"', 5, .))
display `"if_expr: `if_expr'"'

// Check _dash_json_str
_dash_json_str "`if_expr'" _jif
display `"_jif: `_jif'"'
