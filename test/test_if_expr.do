// Test if_expr handling in JSON assembly
sysuse auto, clear
dash clear

// Test 1: single scatter without if condition - works fine
dash scatter mpg weight if rep78==1, mc(navy) name(s1) title("Test1")
display "s1 registered"

// Test 2: two scatter without if  
dash scatter mpg weight, mc(navy) name(s2) title("Test2")
display "s2 registered"

// Test: what does the JSON look like?
local j = `"${dash_json_s1}"'
display "Length of s1 json: " strlen(`"`j'"')
// Can we build with just s1?
dash build, saving("if_test.html") title("Test") layout(auto) replace
display "Build with s1 (which has if) succeeded"
