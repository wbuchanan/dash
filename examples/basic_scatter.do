*! basic_scatter.do
*! Example: single interactive scatter plot using dash.
*!
*! Usage:  do examples/basic_scatter.do
*!         (run from the dash/ directory)
*!
*! Produces: scatter.html — opens in default browser automatically.
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
// Basic scatter with marker color and plot title
// ----------------------------------------------------------------
dash scatter mpg weight, ///
    mc(navy) ms(circle) msi(medium)     ///
    title("Fuel Efficiency vs. Weight") ///
    xtitle("Weight (lbs.)")             ///
    ytitle("Mileage (mpg)")             ///
    saving("scatter.html")

// The file scatter.html is opened in your default browser automatically.
// To save without opening the browser, change saving() to a full path
// and omit the browse option.
