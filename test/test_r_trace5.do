sysuse auto, clear
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado"

_dash_parse_varpart_std mpg weight if rep78==1
local if_cl `"`s(if_clause)'"'
display "if_cl length: " strlen(`"`if_cl'"')
display "if_cl char 1: [" substr(`"`if_cl'"',1,1) "] = " ascii(substr(`"`if_cl'"',1,1))
display "if_cl char 2: [" substr(`"`if_cl'"',2,1) "] = " ascii(substr(`"`if_cl'"',2,1))
display "if_cl char 3: [" substr(`"`if_cl'"',3,1) "] = " ascii(substr(`"`if_cl'"',3,1))
display "if_cl char 4: [" substr(`"`if_cl'"',4,1) "] = " ascii(substr(`"`if_cl'"',4,1))
display "if_cl char 5: [" substr(`"`if_cl'"',5,1) "] = " ascii(substr(`"`if_cl'"',5,1))
display "if_cl char 6: [" substr(`"`if_cl'"',6,1) "] = " ascii(substr(`"`if_cl'"',6,1))
display "if_cl substr(4,.): [" substr(`"`if_cl'"',4,.) "]"
display "if_cl substr(5,.): [" substr(`"`if_cl'"',5,.) "]"
