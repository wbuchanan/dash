sysuse auto, clear
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado"

_dash_parse_varpart_std mpg weight if rep78==1
local if_cl `"`s(if_clause)'"'
display "if_cl len=" strlen(`"`if_cl'"')

// Show each character safely
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"`if_cl'"'
file close `fh'
display "if_cl value:"
type "`tf'"
display "---"

// What does substr(4) give?
display "substr(4,.): [" substr(`"`if_cl'"',4,.) "]"
// What does substr(5) give?
display "substr(5,.): skipping..."

// Correct fix - use strtrim to handle variable spacing
local if_expr = strtrim(subinstr(`"`if_cl'"', "if ", "", 1))
display "via subinstr: [" `"`if_expr'"' "]"
