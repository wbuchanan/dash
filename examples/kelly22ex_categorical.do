*! kelly22ex_categorical.do
*! Example: categorical variable encoding using the kelly22ex color scheme.
*!
*! Demonstrates using kelly22ex RGB colors to encode the rep78 repair-record
*! variable (categories 1-5) with distinct colors and marker shapes per group.
*!
*! Usage:  do examples/kelly22ex_categorical.do
*!         (run from the dash/ directory)
*!
*! Requires: kelly22ex scheme installed
*!   (typically at: ~/Library/Application Support/Stata/ado/plus/s/)
*!
*! Produces: kelly22ex_dashboard.html
*!
*! kelly22ex palette (p1-p5 colors used here):
*!   p1 = "242 194  44"  — vivid yellow
*!   p2 = "134  88 145"  — strong purple
*!   p3 = "241 132  34"  — vivid orange
*!   p4 = "162 203 239"  — light blue
*!   p5 = "188   9  53"  — vivid red
*!
*! Version: 1.0.0  28mar2026

// ----------------------------------------------------------------
// Load data
// ----------------------------------------------------------------
sysuse auto, clear

// ----------------------------------------------------------------
// Clear any existing dash registry
// ----------------------------------------------------------------
dash clear

// ================================================================
// DEFINE GRAPHS
// ================================================================

// --- Graph 1: MPG vs Weight — rep78 categories encoded by kelly22ex colors ---
// Each repair-record group (1-5) uses a distinct kelly22ex color and marker.
dash (scatter mpg weight if rep78==1, mc("242 194 44")  ms(circle)            msi(medsmall)) ///
     (scatter mpg weight if rep78==2, mc("134 88 145")  ms(square)            msi(medsmall)) ///
     (scatter mpg weight if rep78==3, mc("241 132 34")  ms(triangle)          msi(medsmall)) ///
     (scatter mpg weight if rep78==4, mc("162 203 239") ms(diamond)           msi(medsmall)) ///
     (scatter mpg weight if rep78==5, mc("188 9 53")    ms(inverted_triangle) msi(medsmall)), ///
     name(s1)                                ///
     title("MPG vs Weight by Repair Record") ///
     subtitle("kelly22ex color encoding")    ///
     xtitle("Weight (lbs.)")                 ///
     ytitle("Mileage (mpg)")

// --- Graph 2: Price vs Weight — rep78 categories (same kelly22ex palette) ---
dash (scatter price weight if rep78==1, mc("242 194 44")  ms(circle)            msi(medsmall)) ///
     (scatter price weight if rep78==2, mc("134 88 145")  ms(square)            msi(medsmall)) ///
     (scatter price weight if rep78==3, mc("241 132 34")  ms(triangle)          msi(medsmall)) ///
     (scatter price weight if rep78==4, mc("162 203 239") ms(diamond)           msi(medsmall)) ///
     (scatter price weight if rep78==5, mc("188 9 53")    ms(inverted_triangle) msi(medsmall)), ///
     name(s2)                            ///
     title("Price vs Weight by Repair Record") ///
     xtitle("Weight (lbs.)")             ///
     ytitle("Price ($)")

// --- Graph 3: MPG vs Length — rep78 categories with OLS overlay ---
dash (scatter mpg length if rep78==1, mc("242 194 44")  ms(circle)            msi(medsmall)) ///
     (scatter mpg length if rep78==2, mc("134 88 145")  ms(square)            msi(medsmall)) ///
     (scatter mpg length if rep78==3, mc("241 132 34")  ms(triangle)          msi(medsmall)) ///
     (scatter mpg length if rep78==4, mc("162 203 239") ms(diamond)           msi(medsmall)) ///
     (scatter mpg length if rep78==5, mc("188 9 53")    ms(inverted_triangle) msi(medsmall)) ///
     (lfit    mpg length,              lc(black)        lw(thick)),            ///
     name(s3)                                    ///
     title("MPG vs Length by Repair Record")     ///
     xtitle("Length (in.)")                      ///
     ytitle("Mileage (mpg)")

// --- Graph 4: MPG distribution (histogram) ---
dash histogram mpg, ///
     name(h1)       ///
     title("MPG Distribution") ///
     xtitle("Mileage (mpg)")   ///
     ytitle("Count")

// ================================================================
// DEFINE KPI CARDS
// ================================================================

// Average MPG
dash kpi mean(mpg),            ///
     title("Avg MPG")          ///
     name(k1)                  ///
     fmt(%9.1f)                ///
     subtitle("Miles per gallon") ///
     update(filter)

// Average price
dash kpi mean(price),          ///
     title("Avg Price")        ///
     name(k2)                  ///
     fmt(%12.0fc)              ///
     subtitle("1978 USD")      ///
     update(filter)

// Sample size
dash kpi count(mpg),           ///
     title("Sample Size")      ///
     name(k3)                  ///
     fmt(%9.0fc)               ///
     subtitle("Observations")  ///
     update(filter)

// ================================================================
// BUILD DASHBOARD
// ================================================================
dash build,                                         ///
     saving("kelly22ex_dashboard.html")             ///
     title("Repair Record Analysis")                ///
     subtitle("kelly22ex categorical color scheme") ///
     layout(3 2)                                    ///
     link(s1 s2 s3)                                 ///
     filter(foreign, type(dropdown))                ///
     theme(clean)                                   ///
     replace

// ----------------------------------------------------------------
// kelly22ex_dashboard.html features:
//
//   Color legend (rep78 repair record):
//     yellow  circle            = Rep 1 (poor)
//     purple  square            = Rep 2
//     orange  triangle          = Rep 3 (average)
//     lt.blue diamond           = Rep 4
//     red     inverted_triangle = Rep 5 (excellent)
//
//   Linked brushing:
//     Select in s1 to highlight matching points in s2 and s3.
//
//   Filter:
//     Dropdown to switch between Domestic and Foreign cars.
// ----------------------------------------------------------------
