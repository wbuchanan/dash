*! multi_graph_dashboard.do
*! Example: multi-graph dashboard with linked brushing and KPI cards.
*!
*! Usage:  do examples/multi_graph_dashboard.do
*!         (run from the dash/ directory)
*!
*! Produces: dashboard.html — interactive dashboard with 4 graphs,
*!           2 KPI cards, a dropdown filter, and linked brushing.
*! Version: 1.1.0  28mar2026

// ----------------------------------------------------------------
// Setup
// ----------------------------------------------------------------
// Run dash_setup once if you haven't already:
// dash_setup

// ----------------------------------------------------------------
// Load data
// ----------------------------------------------------------------
sysuse auto, clear

// ----------------------------------------------------------------
// Clear any existing dash registry
// ----------------------------------------------------------------
dash clear

// ----------------------------------------------------------------
// Define graphs
// ----------------------------------------------------------------

// Graph 1: MPG vs Weight (scatter + OLS fit line)
dash (scatter mpg weight, mc(navy) msi(small))     ///
     (lfit mpg weight, lc(maroon) lw(medthick)),   ///
     name(s1) title("MPG vs Weight")               ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// Graph 2: MPG vs Length (scatter only) — note: only ONE comma, separating
// the varlist+plot options from the graph-level options
dash scatter mpg length, ///
    mc(forest_green) msi(small) ///
    name(s2) title("MPG vs Length") ///
    xtitle("Length (in.)") ytitle("Mileage (mpg)")

// Graph 3: MPG vs Weight by repair record (categorical encoding)
// Each rep78 value (1-5) gets a distinct color and marker shape.
dash (scatter mpg weight if rep78==1, mc(navy)         ms(circle)            msi(small)) ///
     (scatter mpg weight if rep78==2, mc(maroon)       ms(square)            msi(small)) ///
     (scatter mpg weight if rep78==3, mc(forest_green) ms(triangle)          msi(small)) ///
     (scatter mpg weight if rep78==4, mc(orange)       ms(diamond)           msi(small)) ///
     (scatter mpg weight if rep78==5, mc(purple)       ms(V) msi(small)), ///
     name(s3) title("MPG vs Weight by Repair Record") ///
     xtitle("Weight (lbs.)") ytitle("Mileage (mpg)")

// Graph 4: MPG Distribution (histogram)
dash histogram mpg, name(h1) title("MPG Distribution") ///
    xtitle("Mileage (mpg)")

// ----------------------------------------------------------------
// Define KPI cards
// ----------------------------------------------------------------

// Average MPG across all cars
dash kpi mean(mpg),  title("Average MPG")  name(k1) ///
    fmt(%9.1f) subtitle("All vehicles") update(filter)

// Number of observations currently visible
dash kpi count(mpg), title("Sample Size") name(k2) ///
    fmt(%9.0fc) update(filter)

// ----------------------------------------------------------------
// Build dashboard
// ----------------------------------------------------------------
dash build,                             ///
    saving("dashboard.html")            ///
    title("Auto Dataset Dashboard")     ///
    subtitle("1978 Automobile Data")    ///
    layout(3 2)                         ///
    link(s1 s2 s3)                      ///
    filter(foreign, type(dropdown))     ///
    theme(clean)                        ///
    replace

// ----------------------------------------------------------------
// The dashboard.html file is opened in your default browser.
//
// Interactive features:
//   - Use the dropdown filter to switch between Domestic and Foreign cars.
//   - Use box-select or lasso-select in graph s1 to highlight the same
//     observations in graphs s2 and s3 (linked brushing across all three).
//   - Graph s3 shows repair record categories encoded by color and shape:
//       navy circle    = Rep 1
//       maroon square  = Rep 2
//       green triangle = Rep 3
//       orange diamond = Rep 4
//       purple V = Rep 5
//   - Hover over any data point to see the variable values.
//   - Pan and zoom with the toolbar icons.
// ----------------------------------------------------------------
