*! full_dashboard.do
*! Fully-commented example: KPIs, multiple graphs, filters, and linking.
*! Also serves as a performance benchmark when used with large datasets.
*!
*! Usage:  do examples/full_dashboard.do
*!         (run from the dash/ directory)
*!
*! Produces: full_dashboard.html
*!
*! To benchmark with 100K rows instead of auto.dta:
*!   local use_large = 1
*!
*! Version: 1.0.0  25mar2026

// ----------------------------------------------------------------
// Configuration
// ----------------------------------------------------------------
// Set to 1 to generate a large synthetic dataset for benchmarking.
// Set to 0 (default) to use the standard auto.dta.
local use_large = 0

// ----------------------------------------------------------------
// Load data
// ----------------------------------------------------------------
if `use_large' == 1 {
    // Generate 100K synthetic observations for performance testing
    clear
    set obs 100000
    set seed 12345

    gen mpg     = 10 + 30*runiform()
    gen weight  = 1500 + 3500*runiform()
    gen price   = 3000 + 15000*runiform()
    gen length  = 130 + 110*runiform()
    gen rep78   = ceil(5*runiform())
    gen foreign = (runiform() > 0.65)

    label variable mpg     "Mileage (mpg)"
    label variable weight  "Weight (lbs.)"
    label variable price   "Price ($)"
    label variable length  "Length (in.)"
    label variable rep78   "Repair record 1978"
    label variable foreign "Car origin"

    label define origin 0 "Domestic" 1 "Foreign"
    label values foreign origin
}
else {
    sysuse auto, clear
}

// ----------------------------------------------------------------
// Record start time for benchmarking
// ----------------------------------------------------------------
local start_time = clock(c(current_time), "hms")

// ----------------------------------------------------------------
// Clear any existing dash registry
// ----------------------------------------------------------------
dash clear

// ================================================================
// DEFINE GRAPHS
// ================================================================

// --- Graph 1: MPG vs Weight with OLS fit line ---
dash (scatter mpg weight, mc(navy) msi(small) ms(circle))   ///
     (lfit    mpg weight, lc(maroon) lw(medthick)),          ///
     name(s1)                                                ///
     title("Fuel Efficiency vs. Weight")                     ///
     xtitle("Weight (lbs.)")                                 ///
     ytitle("Mileage (mpg)")

// --- Graph 2: Price distribution (histogram) ---
dash histogram price,             ///
     name(h1)                     ///
     title("Price Distribution")  ///
     xtitle("Price ($)")          ///
     ytitle("Count")

// --- Graph 3: MPG vs Length (scatter) ---
dash scatter mpg length,           ///
     mc(forest_green) msi(small),  ///
     name(s2)                      ///
     title("MPG vs Car Length")    ///
     xtitle("Length (in.)")        ///
     ytitle("Mileage (mpg)")

// --- Graph 4: MPG density estimate ---
dash kdensity mpg,                  ///
     name(d1)                       ///
     title("MPG Kernel Density")    ///
     xtitle("Mileage (mpg)")        ///
     ytitle("Density")

// ================================================================
// DEFINE KPI CARDS
// ================================================================

// Average MPG — updates when filter changes
dash kpi mean(mpg),                 ///
     title("Avg MPG")               ///
     name(k1)                       ///
     fmt(%9.1f)                     ///
     subtitle("Miles per gallon")   ///
     color(#2c3e50)                 ///
     bgcolor(#ecf0f1)               ///
     update(filter)

// Median price — updates when filter changes
dash kpi median(price),             ///
     title("Median Price")          ///
     name(k2)                       ///
     fmt(%12.0fc)                   ///
     subtitle("1978 USD")           ///
     update(filter)

// Sample size — updates on both filter and brush
dash kpi count(mpg),                ///
     title("Sample Size")           ///
     name(k3)                       ///
     fmt(%9.0fc)                    ///
     subtitle("Observations")       ///
     update(both)

// Distinct repair records
dash kpi dcount(rep78),             ///
     title("Repair Ratings")        ///
     name(k4)                       ///
     fmt(%9.0f)                     ///
     subtitle("Distinct values")    ///
     update(filter)

// ================================================================
// BUILD DASHBOARD
// ================================================================
dash build,                                                  ///
     saving("full_dashboard.html")                           ///
     title("Automobile Data — Interactive Dashboard")        ///
     subtitle("Explore fuel efficiency, pricing, and more")  ///
     layout(3 2)                                             ///
     link(s1 s2)                                             ///
     filter(foreign, type(dropdown))                         ///
     filter(weight, type(range) exclude(h1 d1 k1 k2))       ///
     theme(clean)                                            ///
     replace

// ----------------------------------------------------------------
// Report benchmark time
// ----------------------------------------------------------------
local end_time  = clock(c(current_time), "hms")
local elapsed   = (`end_time' - `start_time') / 1000
display as text "Render time: " %9.2f `elapsed' " seconds"

if `use_large' == 1 {
    display as text "(100,000 observation benchmark)"
    if `elapsed' < 30 {
        display as text "PASS: rendered in under 30 seconds"
    }
    else {
        display as error "WARN: render time exceeded 30 second target"
    }
}

// ----------------------------------------------------------------
// Interactive features in full_dashboard.html:
//
//   Filters:
//     - Dropdown: switch between Domestic and Foreign cars
//     - Range slider: filter by vehicle weight
//       (excludes histogram h1, density d1, and KPIs k1/k2
//        which show overall statistics)
//
//   Linked brushing:
//     - Select observations in graph s1 (MPG vs Weight) to
//       highlight the same cars in graph s2 (MPG vs Length)
//
//   KPI cards:
//     - k1 (Avg MPG), k2 (Median Price), k3 (Sample Size) update
//       when the foreign filter changes
//     - k3 (Sample Size) also updates when you brush-select
//       observations in any linked graph
//
//   All graphs:
//     - Hover for variable values
//     - Pan, zoom, reset, box-select, lasso-select toolbars
// ----------------------------------------------------------------
