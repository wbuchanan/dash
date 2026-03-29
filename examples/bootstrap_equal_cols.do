*! bootstrap_equal_cols.do
*! Example: Bootstrap auto-layout — equal columns, KPIs in first row.
*!
*! The simplest Bootstrap layout: layout(bs) assigns equal column spans
*! automatically. KPI cards always appear in the first row; graphs fill
*! subsequent rows at 2-3 per row depending on count.
*!
*! Usage:  do examples/bootstrap_equal_cols.do
*!         (run from the dash/ directory)
*!
*! Produces: bs_equal_cols.html
*! Version: 1.0.0  29mar2026

sysuse auto, clear
dash clear

// KPI cards
dash kpi mean(mpg),   name(k1) title("Avg MPG")    fmt(%9.1f) subtitle("All vehicles")
dash kpi count(mpg),  name(k2) title("Sample Size") fmt(%9.0fc)
dash kpi mean(price), name(k3) title("Avg Price")   fmt(%9.0fc) subtitle("USD")
dash kpi mean(weight),name(k4) title("Avg Weight")  fmt(%9.0fc) subtitle("lbs")

// Graphs
dash scatter mpg weight, name(s1) title("MPG vs Weight")
dash scatter mpg length, name(s2) title("MPG vs Length")
dash histogram mpg,       name(h1) title("MPG Distribution")

// layout(bs) — auto Bootstrap layout
// Result: Row 1 = 4 KPI cards (col-3 each)
//         Row 2 = s1 + s2 (col-6 each)
//         Row 3 = h1 (col-6)
dash build,                         ///
    saving("bs_equal_cols.html")    ///
    title("Auto Dataset — Equal Columns") ///
    layout(bs)                      ///
    replace
