*! bootstrap_responsive.do
*! Example: Bootstrap responsive asymmetric layout with filter widgets.
*!
*! Demonstrates combining Bootstrap grid layout with filter() and link()
*! options. The layout adapts to screen width: on large screens the main
*! scatter occupies 8 columns beside a 4-column sidebar; on small screens
*! both stack to full width via the db-col-12 fallback.
*!
*! Layout:
*!   Row 1: k1=4 k2=4 k3=4           (three KPI cards)
*!   Row 2: s1=8 h1=4                (main chart + sidebar histogram)
*!   Row 3: s2=6 s3=6                (two linked scatter plots)
*!
*! Usage:  do examples/bootstrap_responsive.do
*!         (run from the dash/ directory)
*!
*! Produces: bs_responsive.html
*! Version: 1.0.0  29mar2026

sysuse auto, clear
dash clear

// KPI cards (update with filter)
dash kpi mean(mpg),   name(k1) title("Avg MPG")    fmt(%9.1f)  update(filter)
dash kpi count(mpg),  name(k2) title("Sample Size") fmt(%9.0fc) update(filter)
dash kpi mean(price), name(k3) title("Avg Price")   fmt(%9.0fc) update(filter)

// Main scatter
dash (scatter mpg weight, mc(navy) msi(small))    ///
     (lfit   mpg weight, lc(maroon) lw(medthick)), ///
     name(s1) title("MPG vs Weight")               ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// Sidebar histogram
dash histogram mpg, name(h1) title("MPG Distribution")

// Linked secondary plots
dash scatter mpg length, name(s2) title("MPG vs Length")
dash scatter mpg price,  name(s3) title("MPG vs Price")

// Build with Bootstrap layout + filter + linked brushing
dash build,                                                         ///
    saving("bs_responsive.html")                                    ///
    title("Auto Dataset — Responsive Layout")                       ///
    subtitle("Filter by origin; brush s1 to highlight s2 and s3")  ///
    layout(bs: k1=4 k2=4 k3=4 / s1=8 h1=4 / s2=6 s3=6)            ///
    filter(foreign, type(dropdown))                                 ///
    link(s1 s2 s3)                                                  ///
    replace
