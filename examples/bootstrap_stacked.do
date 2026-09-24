*! bootstrap_stacked.do
*! Example: Bootstrap stacked layout — single-column full-width panels.
*!
*! All graphs stacked vertically, each occupying the full row width.
*! Useful for narrative dashboards where each chart tells part of a story
*! and the reader scrolls through in sequence.
*!
*! Layout:
*!   Row 1: k1=3 k2=3 k3=3 k4=3   (KPI summary row)
*!   Row 2: s1=12                  (full-width scatter)
*!   Row 3: h1=12                  (full-width histogram)
*!   Row 4: s2=12                  (full-width categorical scatter)
*!
*! Usage:  do examples/bootstrap_stacked.do
*!         (run from the dash/ directory)
*!
*! Produces: bs_stacked.html
*! Version: 1.0.0  29mar2026

sysuse auto, clear
dash clear

// KPI summary row
dash kpi mean(mpg),    name(k1) title("Avg MPG")    fmt(%9.1f)
dash kpi count(mpg),   name(k2) title("N Cars")     fmt(%9.0fc)
dash kpi mean(price),  name(k3) title("Avg Price")  fmt(%9.0fc) subtitle("USD")
dash kpi mean(weight), name(k4) title("Avg Weight") fmt(%9.0fc) subtitle("lbs")

// Full-width graphs
dash scatter mpg weight, name(s1) title("MPG vs Weight — All Vehicles")  ///
    xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

dash histogram mpg, name(h1) title("Distribution of Fuel Economy") ///
    xtitle("Mileage (mpg)")

// Categorical: one layer per rep78 value
dash (scatter mpg weight if rep78==1, mc(navy)         ms(circle))   ///
     (scatter mpg weight if rep78==2, mc(maroon)       ms(square))   ///
     (scatter mpg weight if rep78==3, mc(forest_green) ms(triangle)) ///
     (scatter mpg weight if rep78==4, mc(orange)       ms(diamond))  ///
     (scatter mpg weight if rep78==5, mc(purple)       ms(V)), ///
     name(s2) title("MPG vs Weight by Repair Record") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// Full-width stacked layout
dash build,                                                                   ///
    saving("bs_stacked.html")                                                ///
    title("Auto Dataset — Stacked Layout")                                   ///
    subtitle("Narrative dashboard: scroll through each chart in sequence")   ///
    layout(bs: k1=3 k2=3 k3=3 k4=3 / s1=12 / h1=12 / s2=12)                ///
    replace
