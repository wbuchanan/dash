// Minimal test - just assembly of graphs_json
sysuse auto, clear
dash clear

// Just s1 with if condition - test graph_json assembly manually
dash scatter mpg weight if rep78==1, mc(navy) name(s1) title("Test1")

// Print the JSON raw using file write (avoids Stata display parsing)
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"${dash_json_s1}"'
file close `fh'
type "`tf'"
display "---JSON printed---"

// Now test assembly like _dash_build does it
local graphs_json ""
local n_graphs = 0
local gname "s1"
if `n_graphs' > 0 local graphs_json = `"`graphs_json', "'
local graphs_json = `"`graphs_json'${dash_json_`gname'}"'
local n_graphs = `n_graphs' + 1

display "graphs_json assembled successfully"

// Write it to file to see it
tempfile tf2
tempname fh2
file open `fh2' using "`tf2'", write replace text
file write `fh2' `"`graphs_json'"'
file close `fh2'
type "`tf2'"
