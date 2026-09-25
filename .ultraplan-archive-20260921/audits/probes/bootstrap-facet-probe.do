clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
sysuse auto, clear
dash clear
dash scatter mpg weight, by(foreign) name(f1) title(faceted)
dash scatter price weight, name(f2) title(plain)
dash build, saving("bs_facet.html") layout(bs) replace
dash clear
dash scatter mpg weight, by(foreign) name(f1) title(faceted)
dash scatter price weight, name(f2) title(plain)
dash build, saving("auto_facet.html") layout(auto) replace
di "DONE_BSFACET"
