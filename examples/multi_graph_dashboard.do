*! multi_graph_dashboard.do
*! Example: multi-graph dashboard with linked brushing and KPI cards.
*!
*! Usage:  do examples/multi_graph_dashboard.do
*!         (run from the dash/ directory)
*!
*! Produces: dashboard.html — interactive dashboard with 3 graphs,
*!           2 KPI cards, a dropdown filter, and linked brushing.
*! Version: 1.0.0  25mar2026

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

// Graph 2: MPG vs Length (scatter only)
dash scatter mpg length, ///
    mc(forest_green) msi(small), ///
    name(s2) title("MPG vs Length") ///
    xtitle("Length (in.)") ytitle("Mileage (mpg)")

// Graph 3: MPG Distribution (histogram)
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
    link(s1 s2)                         ///
    filter(foreign, type(dropdown))     ///
    theme(clean)                        ///
    replace

// ----------------------------------------------------------------
// The dashboard.html file is opened in your default browser.
//
// Interactive features:
//   - Use the dropdown filter to switch between Domestic and Foreign cars.
//   - Use box-select or lasso-select in graph s1 to highlight the same
//     observations in graph s2 (linked brushing).
//   - Hover over any data point to see the variable values.
//   - Pan and zoom with the toolbar icons.
// ----------------------------------------------------------------
