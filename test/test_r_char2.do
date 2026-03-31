// Check exact content of dash_json_s1 global
sysuse auto, clear
dash clear

dash scatter mpg weight if rep78==1, mc(navy) name(s1) title("Test1")

// Write global to file without any assignment
tempfile tf_g
tempname fh_g
file open `fh_g' using "`tf_g'", write replace text
file write `fh_g' `"${dash_json_s1}"'
file close `fh_g'
display "=== dash_json_s1 global (direct) ==="
type "`tf_g'"
display "==="

// Now test the = assignment from the global
local graphs_json ""
local n_graphs = 0
local gname "s1"
local graphs_json = `"${dash_json_`gname'}"'

// Write graphs_json via = expansion to file
tempfile tf_a
tempname fh_a
file open `fh_a' using "`tf_a'", write replace text
file write `fh_a' `"`graphs_json'"'
file close `fh_a'
display "=== graphs_json after = assignment ==="
type "`tf_a'"
display "==="
