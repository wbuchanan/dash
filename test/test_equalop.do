sysuse auto, clear

// Test: can we use == in a compound-quoted string expression?
local x = `"rep78==1"'
display "direct compound quote with ==: `x'"

// Test with JSON-like content
local j = `"{"if_expr":"rep78==1"}"'
display "JSON with ==: `j'"

// Test: global containing == then expanding with =
global myglobal = `"rep78==2"'
local y = `"${myglobal}"'
display "global with ==: `y'"

// What if the global has JSON with ==?
global myjson `"{"if_expr":"rep78==2"}"'
local z = `"${myjson}"'
display "via global =:"
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"`z'"'
file close `fh'
type "`tf'"
