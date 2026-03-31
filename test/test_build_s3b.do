// Test dash build with s3 - no display of JSON
sysuse auto, clear

dash clear

dash scatter mpg weight, mc(navy) name(s1) title("Test1")
dash scatter mpg length, mc(maroon) name(s2) title("Test2")

dash (scatter mpg weight if rep78==1, mc(navy)         ms(circle)            msi(small)) ///
     (scatter mpg weight if rep78==2, mc(maroon)       ms(square)            msi(small)) ///
     (scatter mpg weight if rep78==3, mc(forest_green) ms(triangle)          msi(small)) ///
     (scatter mpg weight if rep78==4, mc(orange)       ms(diamond)           msi(small)) ///
     (scatter mpg weight if rep78==5, mc(purple)       ms(inverted_triangle) msi(small)), ///
     name(s3) title("Rep78 Categories") xtitle("Weight") ytitle("MPG")

dash build, saving("s3_test2.html") title("Test") layout(auto) link(s1 s2 s3) filter(foreign, type(dropdown)) theme(clean) replace

display "DONE"
