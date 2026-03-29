*! bootstrap_kpi_hero.do
*! Example: Bootstrap layout with a full-width "hero" featured graph.
*!
*! Demonstrates explicit column-span control: the main scatter plot spans
*! 8 of 12 columns (two-thirds width) next to a narrow side panel.
*!
*! Layout:
*!   Row 1: k1=3  k2=3  k3=3  k4=3   (four KPI cards, equal width)
*!   Row 2: s1=8  h1=4               (featured scatter + narrow histogram)
*!   Row 3: s2=6  s3=6               (two equal scatter plots)
*!
*! Usage:  do examples/bootstrap_kpi_hero.do
*!         (run from the dash/ directory)
*!
*! Produces: bs_kpi_hero.html
*! Version: 1.0.0  29mar2026

sysuse auto, clear
dash clear

// KPI cards
dash kpi mean(mpg),    name(k1) title("Avg MPG")     fmt(%9.1f)  subtitle("All vehicles")
dash kpi count(mpg),   name(k2) title("Sample Size")  fmt(%9.0fc)
dash kpi mean(price),  name(k3) title("Avg Price")    fmt(%9.0fc) subtitle("USD")
dash kpi mean(weight), name(k4) title("Avg Weight")   fmt(%9.0fc) subtitle("lbs")

// Main featured graph (will span 8 of 12 columns)
dash (scatter mpg weight, mc(navy) msi(small))   ///
     (lfit   mpg weight, lc(maroon) lw(medthick)), ///
     name(s1) title("MPG vs Weight (with OLS fit)") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// Side histogram (will span 4 of 12 columns)
dash histogram mpg, name(h1) title("MPG Distribution") xtitle("MPG")

// Secondary graphs (equal width)
dash scatter mpg length, name(s2) title("MPG vs Length")
dash scatter price weight, name(s3) title("Price vs Weight")

// Explicit Bootstrap layout
dash build,                                                         ///
    saving("bs_kpi_hero.html")                                     ///
    title("Auto Dataset — Hero Layout")                            ///
    subtitle("Featured: MPG vs Weight")                            ///
    layout(bs: k1=3 k2=3 k3=3 k4=3 / s1=8 h1=4 / s2=6 s3=6)     ///
    replace
