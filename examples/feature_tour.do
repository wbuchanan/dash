*! feature_tour.do
*! Example: the options and plot types the other examples do not reach.
*!
*! WHY THIS EXISTS
*!   A feature with no example is a feature nobody tries.  Measured across
*!   the other ten examples before this file was written: scheme() appeared
*!   in two, tabs() in one, colorvar() in one, and bin(), level(), kernel(),
*!   bwidth(), legend(), xline(), note(), mlabel(), xlabel(), yaxis(),
*!   hover(), jitter(), function and a multi-variable varlist appeared in
*!   none.  Ten of dash's forty plot types appeared in no example at all
*!   before examples/plot_types_tour.do, which now draws every type; this
*!   file keeps the options tour.  `dash serve' is shown in
*!   examples/serve_dashboard.do.
*!
*! Usage:  do examples/feature_tour.do
*!         (run from the dash/ directory)
*!
*! Produces: feature_tour.html
*! Version: 0.1.0  13nov2026

sysuse auto, clear
dash clear

// ----------------------------------------------------------------
// A varlist with more than one y variable draws one series each,
// exactly as twoway does.
// ----------------------------------------------------------------
dash scatter mpg turn weight,          ///
    title("Two series from one varlist")   ///
    legend(position(3))                    ///
    name(multi)

// ----------------------------------------------------------------
// Statistical layers, each with the option that controls it.
// ----------------------------------------------------------------
dash histogram price, bin(12) percent  ///
    title("Explicit bin count")            ///
    note("bin(12) percent")                ///
    name(hist)

dash kdensity mpg, kernel(gaussian) bwidth(2) range(5 45) ///
    title("A chosen kernel and bandwidth")                    ///
    name(kde)

dash (scatter mpg weight)              ///
     (lfitci  mpg weight, level(90)),  ///
    title("A 90% band, not the default 95%")                  ///
    name(fit)

// ----------------------------------------------------------------
// A drawn function, and a secondary axis.
// ----------------------------------------------------------------
dash (function 2000 + 400*sin(x), range(0 20))  ///
     (scatter price rep78),                     ///
    title("A function over the data")               ///
    name(fn)

dash (line price weight)                        ///
     (line mpg weight, yaxis(2)),               ///
    title("Two scales, one x axis")                 ///
    ytitle("Mileage (mpg)", axis(2))                ///
    name(twoaxis)

// ----------------------------------------------------------------
// Paired coordinates: four variables, and literal points.
// ----------------------------------------------------------------
generate double w2 = weight + 300
generate double m2 = mpg + 4
dash pcspike mpg weight m2 w2,        ///
    title("Paired coordinates")           ///
    name(pcs)

// ----------------------------------------------------------------
// Axis vocabulary, reference lines, and annotation.
// ----------------------------------------------------------------
dash scatter mpg weight,               ///
    xlabel(#8, grid)                       ///
    ylabel(10(5)45, format(%9.0f))         ///
    xline(3000) yline(20)                  ///
    mlabel(make) mlabsize(small)           ///
    note("xlabel(#8, grid), reference lines and marker labels")   ///
    caption("Source: 1978 Automobile Data")                       ///
    name(axes)

// ----------------------------------------------------------------
// Faceting, jitter with a reproducible seed, and a colour variable.
// ----------------------------------------------------------------
dash scatter mpg weight, by(foreign)   ///
    jitter(4) jitterseed(20260920)         ///
    title("Faceted, with reproducible jitter")   ///
    name(facets)

dash scatter mpg weight,               ///
    colorvar(price) colorlevels(8)                       ///
    colorlist("68 1 84" "70 50 126" "54 92 141" "39 127 142"   ///
              "31 161 135" "74 193 109" "160 218 57" "253 231 37")   ///
    title("Coloured by a third variable")                ///
    name(cvar)

// ----------------------------------------------------------------
// KPI cards, including the four statistics the help used to omit.
// ----------------------------------------------------------------
dash kpi mean(price),     title("Mean price")   fmt(%9.0fc) name(k1)
dash kpi var(price),      title("Variance")     fmt(%12.0fc) name(k2)
dash kpi cv(price),       title("CV")           fmt(%9.3f)  name(k3)
dash kpi iqr(price),      title("IQR")          fmt(%9.0fc) name(k4)
dash kpi skewness(price), title("Skewness")     fmt(%9.3f)  name(k5)
dash kpi p90(price),      title("90th pct")     fmt(%9.0fc) name(k6)

// ----------------------------------------------------------------
// Build it: a named scheme, tabs, a left sidebar, and two filters.
// ----------------------------------------------------------------
dash build,                                                        ///
    saving("feature_tour.html") replace                            ///
    title("dash feature tour")                                     ///
    subtitle("Every option the other examples do not reach")       ///
    scheme(s1color)                                                ///
    layout(bs)                                                     ///
    filterposition(left)                                           ///
    filter(foreign, type(dropdown) label("Origin"))                ///
    filter(price, type(range) exclude(k1 k2 k3 k4 k5 k6))          ///
    link(_all)                                                     ///
    tabs(Distributions: hist kde k1 k2 k3 /                        ///
         Relationships: multi fit fn twoaxis axes /                ///
         Groups: facets cvar pcs k4 k5 k6)

display as text "feature_tour.do: wrote feature_tour.html"
