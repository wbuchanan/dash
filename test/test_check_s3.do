sysuse auto, clear
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash_parse.mata"
do "/Users/billy/Desktop/Programs/StataPrograms/d/dash/dash.ado"

dash clear

dash (scatter mpg weight if rep78==1, mc(navy)         ms(circle)            msi(small)) ///
     (scatter mpg weight if rep78==2, mc(maroon)       ms(square)            msi(small)), ///
     name(s3) title("Test") xtitle("Weight") ytitle("MPG")

// Write s3 JSON to file  
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"${dash_json_s3}"'
file close `fh'
display "=== dash_json_s3 ==="
type "`tf'"
display "==="

// Now assemble graphs_json WITHOUT =
local graphs_json ""
local n_graphs = 0
local gname "s3"
local graphs_json `"`graphs_json'${dash_json_`gname'}"'
local n_graphs = `n_graphs' + 1

// Write to file
tempfile tf2
tempname fh2
file open `fh2' using "`tf2'", write replace text
file write `fh2' `"`graphs_json'"'
file close `fh2'
display "=== graphs_json after assembly ==="
type "`tf2'"
display "==="
