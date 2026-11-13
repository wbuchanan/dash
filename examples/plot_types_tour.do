*! plot_types_tour.do
*! Example: every plot type dash draws, one graph each, a weighted layer
*! and a page with a Download CSV button.
*!
*! WHY THIS EXISTS
*!   Before this file, ten of dash's plot types (bar, scatteri, pci,
*!   pcarrowi, pccapsym, pcbarrow, pcscatter, tsline, tsrline, fpfit)
*!   appeared in no example, and no example used a weight or csv.  Each
*!   graph below is the shortest command that draws its type; copy the one
*!   you need.  test/test_examples_cover.py reads the drawn types from
*!   dash.ado and fails when one of them has no example.
*!
*! Usage:  do examples/plot_types_tour.do
*!         (run from the dash/ directory)
*!
*! Produces: plot_types_tour.html, plot_types_tour_ts.html
*! Version: 0.1.0  13nov2026

sysuse auto, clear
dash clear

// Variables the range and paired-coordinate types need.
sort weight
generate double mpg_lo = mpg - 3
generate double mpg_hi = mpg + 3
generate double w2     = weight + 300
generate double m2     = mpg + 4

// ----------------------------------------------------------------
// Points, lines and areas.
// ----------------------------------------------------------------
dash scatter   mpg weight,  title("scatter")   name(pt01)
dash line      mpg weight,  title("line")      name(pt02)
dash connected mpg weight,  title("connected") name(pt03)
dash area      mpg weight,  title("area")      name(pt04)
dash bar       mpg foreign, title("bar")       name(pt05)
dash spike     mpg weight,  title("spike")     name(pt06)
dash dropline  mpg weight,  title("dropline")  name(pt07)
dash dot       mpg rep78,   title("dot")       name(pt08)
dash scatteri  20 2000 30 4000, title("scatteri") name(pt09)

// ----------------------------------------------------------------
// Fits and smoothers.
// ----------------------------------------------------------------
dash lfit    mpg weight, title("lfit")    name(pt10)
dash qfit    mpg weight, title("qfit")    name(pt11)
dash fpfit   mpg weight, title("fpfit")   name(pt12)
dash lfitci  mpg weight, title("lfitci")  name(pt13)
dash qfitci  mpg weight, title("qfitci")  name(pt14)
dash fpfitci mpg weight, title("fpfitci") name(pt15)
dash lowess  mpg weight, title("lowess")  name(pt16)
dash lpoly   mpg weight, title("lpoly")   name(pt17)
dash lpolyci mpg weight, title("lpolyci") name(pt18)
dash mspline mpg weight, title("mspline") name(pt19)
dash mband   mpg weight, title("mband")   name(pt20)

// ----------------------------------------------------------------
// Distributions and a drawn function.
// ----------------------------------------------------------------
dash histogram price, title("histogram") name(pt21)
dash kdensity  mpg,   title("kdensity")  name(pt22)
dash function  2000 + 400*sin(x), range(0 20) title("function") name(pt23)

// ----------------------------------------------------------------
// Ranges: y1 y2 x, and y1 y2 y3 x for rpcap and rpspike.
// ----------------------------------------------------------------
dash rarea      mpg_lo mpg_hi weight, title("rarea")      name(pt24)
dash rbar       mpg_lo mpg_hi weight, title("rbar")       name(pt25)
dash rspike     mpg_lo mpg_hi weight, title("rspike")     name(pt26)
dash rcap       mpg_lo mpg_hi weight, title("rcap")       name(pt27)
dash rcapsym    mpg_lo mpg_hi weight, title("rcapsym")    name(pt28)
dash rline      mpg_lo mpg_hi weight, title("rline")      name(pt29)
dash rconnected mpg_lo mpg_hi weight, title("rconnected") name(pt30)
dash rscatter   mpg_lo mpg_hi weight, title("rscatter")   name(pt31)
dash rpcap      mpg_lo mpg_hi mpg weight, title("rpcap")  name(pt32)
dash rpspike    mpg_lo mpg_hi mpg weight, title("rpspike") name(pt33)

// ----------------------------------------------------------------
// Paired coordinates: y1 x1 y2 x2, and literal points.
// ----------------------------------------------------------------
dash pcspike   mpg weight m2 w2, title("pcspike")   name(pt34)
dash pcarrow   mpg weight m2 w2, title("pcarrow")   name(pt35)
dash pcbarrow  mpg weight m2 w2, title("pcbarrow")  name(pt36)
dash pccapsym  mpg weight m2 w2, title("pccapsym")  name(pt37)
dash pcscatter mpg weight m2 w2, title("pcscatter") name(pt38)
dash pci       20 2000 30 4000,  title("pci")       name(pt39)
dash pcarrowi  20 2000 30 4000,  title("pcarrowi")  name(pt40)

// ----------------------------------------------------------------
// Surfaces: z y x.
// ----------------------------------------------------------------
dash contour     price mpg weight in 1/50, title("contour")     name(pt41)
dash contourline price mpg weight in 1/50, title("contourline") name(pt42)

// ----------------------------------------------------------------
// A weighted layer: analytic weights size the markers, as in twoway.
// ----------------------------------------------------------------
dash scatter mpg weight [aw=price], title("scatter [aw=price]") ///
    name(pt_weighted)

// ----------------------------------------------------------------
// Build it; csv adds a Download CSV button for the rows the filters
// leave.
// ----------------------------------------------------------------
dash build,                                             ///
    saving("plot_types_tour.html") csv replace          ///
    title("dash plot types tour")                       ///
    subtitle("Every plot type dash draws, one graph each")

// ----------------------------------------------------------------
// Time series: tsline and tsrline read the time variable tsset names.
// dash build draws from the data in memory, so these two get a page of
// their own, built while sp500 is loaded.
// ----------------------------------------------------------------
preserve
sysuse sp500, clear
tsset date
dash clear
dash tsline  close,    title("tsline")  name(pt_tsline)
dash tsrline high low, title("tsrline") name(pt_tsrline)
dash build,                                             ///
    saving("plot_types_tour_ts.html") replace           ///
    title("dash plot types tour: time series")
restore

display as text "plot_types_tour.do: wrote plot_types_tour.html and plot_types_tour_ts.html"
