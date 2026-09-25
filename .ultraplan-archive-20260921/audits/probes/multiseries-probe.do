clear all
adopath ++ "/Users/billy/Desktop/Programs/Java/StataJSON"
adopath ++ "/Users/billy/Desktop/Programs/StataPrograms/d/dash"
sysuse auto, clear
dash clear
dash scatter mpg price weight, name(m1) title(three var scatter)
dash build, saving("ms_3var.html") replace
dash clear
dash (scatter mpg weight) (scatter price weight), name(m2) title(two overlaid)
dash build, saving("ms_overlay.html") replace
di "DONE"
