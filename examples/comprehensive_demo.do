*! comprehensive_demo.do
*! Comprehensive showcase of all dash features:
*!   - All supported twoway plot types
*!   - All three filter types (dropdown, range, slider)
*!   - Linked brushing across multiple graphs
*!   - Bootstrap layout with left-sidebar filters
*!   - At least 6 KPI cards
*!   - Three tab panels: Univariate, Bivariate, Multivariate
*!   - by() option for faceted graphs
*!
*! Usage:  do examples/comprehensive_demo.do
*!         (run from the dash/ directory)
*!
*! Produces: comprehensive_demo.html
*! Version: 1.0.0  30mar2026

// ----------------------------------------------------------------
// Setup
// ----------------------------------------------------------------
sysuse auto, clear
dash clear

// Sort by weight so line/connected/area plots have monotone x
sort weight

// Derived variables used by range and paired-coordinate plots
gen mpg_lo  = mpg - 2
gen mpg_hi  = mpg + 2
gen pc_y1   = mpg
gen pc_x1   = weight
gen pc_y2   = mpg  + (foreign == 1) * 4 - (foreign == 0) * 2
gen pc_x2   = weight - 150 + foreign * 300

label var mpg_lo  "MPG lower bound (mpg - 2)"
label var mpg_hi  "MPG upper bound (mpg + 2)"

// ----------------------------------------------------------------
// KPI cards  (6 cards, all update with filter)
// ----------------------------------------------------------------
dash kpi mean(mpg),          name(k1) title("Avg MPG")          ///
    fmt(%9.1f)  subtitle("miles / gallon")   update(filter)
dash kpi count(mpg),         name(k2) title("# Cars")            ///
    fmt(%9.0f)  subtitle("in current filter") update(filter)
dash kpi mean(price),        name(k3) title("Avg Price")         ///
    fmt(%9.0fc) subtitle("USD")              update(filter)
dash kpi mean(weight),       name(k4) title("Avg Weight")        ///
    fmt(%9.0fc) subtitle("lbs")             update(filter)
dash kpi mean(rep78),        name(k5) title("Avg Repair")        ///
    fmt(%9.2f)  subtitle("scale 1 – 5")     update(filter)
dash kpi mean(displacement), name(k6) title("Avg Displ.")        ///
    fmt(%9.0f)  subtitle("cubic inches")    update(filter)

// ================================================================
// UNIVARIATE GRAPHS  (one variable — distribution plots)
// ================================================================

// u1: histogram of MPG
dash histogram mpg, ///
    name(u1) title("MPG Distribution") xtitle("Mileage (mpg)")

// u2: kernel density of MPG
dash kdensity mpg, ///
    name(u2) title("MPG Kernel Density") xtitle("Mileage (mpg)")

// u3: histogram + kdensity overlay on the same axes
dash (histogram mpg, fc(ltblue%40)) ///
     (kdensity  mpg, lc(maroon) lw(medthick)), ///
     name(u3) title("MPG: Histogram + Density Overlay") xtitle("Mileage (mpg)")

// u4: histogram of price
dash histogram price, ///
    name(u4) title("Price Distribution") xtitle("Price (USD)")

// u5: histogram of MPG faceted by car origin  (by() on a univariate plot)
dash histogram mpg, by(foreign) ///
    name(u5) title("MPG by Car Origin") xtitle("Mileage (mpg)")

// ================================================================
// BIVARIATE GRAPHS  (two variables — relationships)
// ================================================================

// b1: scatter + OLS fit line
dash (scatter mpg weight, mc(navy) msi(small))   ///
     (lfit    mpg weight, lc(maroon) lw(medthick)), ///
     name(b1) title("MPG vs Weight: Scatter + OLS") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b2: scatter + Lowess smoother
dash (scatter mpg weight, mc(forest_green) msi(small)) ///
     (lowess  mpg weight, lc(orange) lw(medthick)),     ///
     name(b2) title("MPG vs Weight: Scatter + Lowess")  ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b3: scatter + quadratic fit
dash (scatter mpg weight, mc(purple) msi(small))  ///
     (qfit    mpg weight, lc(teal) lw(medthick)),  ///
     name(b3) title("MPG vs Weight: Quadratic Fit") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b4: scatter + local polynomial
dash (scatter mpg weight, mc(maroon) msi(small))  ///
     (lpoly   mpg weight, lc(forest_green) lw(medthick)), ///
     name(b4) title("MPG vs Weight: Local Polynomial") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b5: scatter + mean spline
dash (scatter mpg weight, mc(orange) msi(small)) ///
     (mspline mpg weight, lc(navy) lw(medthick)), ///
     name(b5) title("MPG vs Weight: Mean Spline")  ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b6: scatter + mean band
dash (scatter mpg weight, mc(navy) msi(small))  ///
     (mband   mpg weight, fc(ltblue%25)),  ///
     name(b6) title("MPG vs Weight: Mean Band")  ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b7: line plot
dash line mpg weight, lc(navy) lw(medthick) ///
     name(b7) title("MPG vs Weight: Line") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b8: connected plot
dash connected mpg rep78, mc(maroon) lc(maroon) ///
     name(b8) title("MPG by Repair Record: Connected") ///
     xtitle("Repair Record") ytitle("Mileage (mpg)")

// b9: area plot
dash area mpg weight, fc(ltblue%50) ///
     name(b9) title("MPG vs Weight: Area") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b10: spike
dash spike mpg weight, lc(navy) ///
     name(b10) title("MPG vs Weight: Spike") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b12: dropline
dash dropline mpg weight, mc(maroon) lc(maroon) ///
     name(b11) title("MPG vs Weight: Dropline") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// b13: dot plot (dotplot of MPG by repair record)
dash dot mpg rep78, mc(navy) ///
     name(b12) title("MPG by Repair Record: Dot") ///
     xtitle("Repair Record") ytitle("Mileage (mpg)")

// b14: rarea  (range area — mpg ± 2 vs weight)
dash rarea mpg_lo mpg_hi weight, fc(ltblue%40) lw(0) ///
     name(b13) title("MPG Range vs Weight: rarea") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2")

// b15: rbar  (range bar)
dash rbar mpg_lo mpg_hi weight, fc(maroon) ///
     name(b14) title("MPG Range vs Weight: rbar") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2")

// b16: rcap  (range cap — confidence-interval caps)
dash rcap mpg_lo mpg_hi weight, lc(navy) ///
     name(b15) title("MPG Range vs Weight: rcap") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2")

// b17: rspike  (range spike)
dash rspike mpg_lo mpg_hi weight, lc(forest_green) ///
     name(b16) title("MPG Range vs Weight: rspike") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2")

// ================================================================
// MULTIVARIATE GRAPHS  (3+ variables, overlaid categories, by(), etc.)
// ================================================================

// m1: scatter color-coded by car origin  (colorvar)
dash scatter mpg weight, colorvar(foreign) colordiscrete ///
     name(m1) title("MPG vs Weight: Color-Coded by Car Origin") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m2: OLS fit with 95% CI band  (scatter + lfitci)
dash (scatter mpg weight, colorvar(foreign) colordiscrete)     ///
     (lfitci  mpg weight, fc(ltblue%30)),     ///
     name(m2) title("OLS Fit with 95% CI (lfitci)") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m3: quadratic fit with 95% CI  (scatter + qfitci)
dash (scatter mpg weight, colorvar(foreign) colordiscrete)   ///
     (qfitci  mpg weight, fc(lavender%30)),   ///
     name(m3) title("Quadratic Fit with 95% CI (qfitci)") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m4: local polynomial with 95% CI  (scatter + lpolyci)
dash (scatter mpg weight, colorvar(foreign) colordiscrete) ///
     (lpolyci mpg weight, fc(lime%30)),            ///
     name(m4) title("Local Poly with 95% CI (lpolyci)")  ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m5: fractional polynomial fit + CI  (scatter + fpfitci)
dash (scatter mpg weight, colorvar(foreign) colordiscrete)  ///
     (fpfitci mpg weight, fc(gold%30)),       ///
     name(m5) title("Fractional Poly Fit + CI (fpfitci)") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m6: scatter with color encoding by repair record
// Uses colorvar() to encode rep78 values as distinct colors
// Note: To use different marker shapes per group, use multiple scatter commands with if conditions
//       (as shown in commented code below). Future versions may support marker shape encoding.
dash scatter mpg weight, colorvar(rep78) colordiscrete ///
     name(m6) title("MPG vs Weight: Color-Coded by Repair Record") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// m7: rconnected  (range connected — mpg ± 2 vs weight)  ★ primary by() example
dash rconnected mpg_lo mpg_hi weight, mc(maroon) lc(maroon) ///
     name(m7) title("MPG Range vs Weight: rconnected (by)") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2") by(foreign)

// m8: rline  (range line)
dash rline mpg_lo mpg_hi weight, lc(navy) ///
     name(m8) title("MPG Range vs Weight: rline") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2") by(foreign)

// m9: rcapsym  (range cap with symmetric decorations)
dash rcapsym mpg_lo mpg_hi weight, mc(maroon) lc(maroon) ///
     name(m9) title("MPG Range vs Weight: rcapsym") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2") by(foreign)

// m10: rscatter  (range scatter plot)
dash rscatter mpg_lo mpg_hi weight, mc(navy) ///
     name(m10) title("MPG Range vs Weight: rscatter") ///
     xtitle("Weight (lbs.)") ytitle("MPG ± 2") by(foreign)

// m11: pcarrow  (paired-coordinate arrows)
// Note: pc_y2/pc_x2 (lines 31-32) encode the domestic-vs-foreign contrast
// directly in the offsets, so this is overlaid (no by()) — faceting would
// degenerate every arrow within a panel into the same parallel offset and
// erase the visual contrast that the offsets were constructed to demonstrate.
dash pcarrow pc_y1 pc_x1 pc_y2 pc_x2, ///
     name(m11) title("Paired-Coordinate Arrows (pcarrow)") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// ================================================================
// BUILD THE DASHBOARD
// ================================================================
//
// Layout:  Bootstrap grid, left sidebar, 6 KPI cards in a top row,
//          three tab panels below.
//
// Filters:
//   - dropdown : foreign  (All / Domestic / Foreign)
//   - range    : mpg      (min – max range slider)
//   - slider   : weight   (weight >= threshold)
//
// Linked brushing: b1 b2 b3 m6  (all plot mpg vs weight; brush one to
//   highlight the same observations in the others)
//
// ================================================================

dash build,                                                         ///
    saving("comprehensive_demo.html")                              ///
    title("Stata dash — Comprehensive Feature Demo")               ///
    subtitle("Auto Dataset · All Plot Types · Filters · Linked Brushing · Tabs") ///
    layout(bs)                                                      ///
    filter(foreign, type(dropdown))                                ///
    filter(mpg,     type(range))                                   ///
    filter(weight,  type(slider))                                  ///
    link(b1 b2 b3 m6)                                              ///
    tabs(univariate:   u1 u2 u3 u4 u5                             ///
       / bivariate:    b1 b2 b3 b4 b5 b6 b7 b8 b9 b10 b11 b12 b13 b14 b15 b16 ///
       / multivariate: m1 m2 m3 m4 m5 m6 m7 m8 m9 m10 m11) ///
    filterposition(left)                                           ///
    replace
