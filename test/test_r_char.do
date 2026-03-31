// Test r character in macro assembly with =
sysuse auto, clear

// Test 1: direct string with rep78
local mystr = `"rep78==1"'
display `"Test1: `mystr'"'

// Test 2: compound quote with if_expr containing rep78
local if_expr "rep78==1"
local seg_json `"{"if_expr":"`if_expr'"}"'
display `"seg_json without =: `seg_json'"'

// Test 3: same with = assignment
local seg_json2 = `"{"if_expr":"`if_expr'"}"'
display `"seg_json with =: `seg_json2'"'

// Test 4: store in global, expand with =
global test_g = `"`seg_json'"'
local assembled = `"${test_g}"'
tempfile tf
tempname fh
file open `fh' using "`tf'", write replace text
file write `fh' `"`assembled'"'
file close `fh'
display "Test 4 (via file):"
type "`tf'"
