{smcl}
{* *! version 1.0.0  25mar2026}{...}
{viewerjumpto "Syntax"            "dash##syntax"}{...}
{viewerjumpto "Description"       "dash##description"}{...}
{viewerjumpto "Differences from twoway" "dash##differences"}{...}
{viewerjumpto "Subcommands"       "dash##subcommands"}{...}
{viewerjumpto "Dashboard Options" "dash##dashboard_options"}{...}
{viewerjumpto "Layout"            "dash##layout"}{...}
{viewerjumpto "Linking and Brushing" "dash##linking"}{...}
{viewerjumpto "Filters"           "dash##filters"}{...}
{viewerjumpto "KPI Cards"         "dash##kpi"}{...}
{viewerjumpto "Server Mode"       "dash##server_mode"}{...}
{viewerjumpto "Examples"          "dash##examples"}{...}
{viewerjumpto "Dependencies"      "dash##dependencies"}{...}
{viewerjumpto "Author"            "dash##author"}{...}
{vieweralsosee "twoway"              "help twoway"}{...}
{vieweralsosee "scatter"             "help scatter"}{...}
{vieweralsosee "line"                "help line"}{...}
{vieweralsosee "connected"           "help connected"}{...}
{vieweralsosee "area"                "help area"}{...}
{vieweralsosee "bar"                 "help bar"}{...}
{vieweralsosee "spike"               "help spike"}{...}
{vieweralsosee "lfit"                "help lfit"}{...}
{vieweralsosee "qfit"                "help qfit"}{...}
{vieweralsosee "lfitci"              "help lfitci"}{...}
{vieweralsosee "qfitci"              "help qfitci"}{...}
{vieweralsosee "lowess"              "help lowess"}{...}
{vieweralsosee "lpoly"               "help lpoly"}{...}
{vieweralsosee "fpfit"               "help fpfit"}{...}
{vieweralsosee "histogram"           "help histogram"}{...}
{vieweralsosee "kdensity"            "help kdensity"}{...}
{vieweralsosee "dash_setup"          "help dash_setup"}{...}
{vieweralsosee "jsonio"              "help jsonio"}{...}

{title:Title}

{phang}
{cmd:dash} {hline 2} Interactive HTML dashboards from {cmd:twoway} syntax


{marker syntax}
{title:Syntax}

{pstd}{ul:Single interactive graph (immediate render)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} [{cmd:,} {it:graph_options}
{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}]

{pstd}{ul:Named graph (accumulate for multi-graph dashboard)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} [{cmd:,} {it:graph_options}
{cmdab:nam:e}{cmd:(}{it:identifier} [{cmd:, replace}]{cmd:)}]

{pstd}{ul:KPI card}{p_end}

{p 8 17 2}
{cmd:dash kpi} {it:statistic}{cmd:(}{it:varname}{cmd:)} {ifin} {cmd:,}
{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:nam:e}{cmd:(}{it:identifier}{cmd:)}
[{cmdab:fmt:}{cmd:(}{it:format}{cmd:)}
{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}
{cmd:color(}{it:color}{cmd:)}
{cmd:bgcolor(}{it:color}{cmd:)}
{cmdab:upd:ate}{cmd:(}{it:mode}{cmd:)}]

{pstd}{ul:Build dashboard (standalone HTML)}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}
[{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}
{cmdab:lay:out}{cmd:(}{it:layout_spec}{cmd:)}
{cmd:link(}{it:namelist} | {cmd:_all}{cmd:)}
{cmd:filter(}{it:varname}{cmd:, type(}{it:filter_type}{cmd:)} [{cmd:exclude(}{it:namelist}{cmd:)}]{cmd:)}
{cmd:theme(}{it:theme_name}{cmd:)}
{cmdab:sch:eme}{cmd:(}{it:schemename}{cmd:)}
{cmd:replace}]

{pstd}{ul:Build Bokeh Server app (write .py file, do not block)}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath.py}{cmd:)}
{cmd:server}
[{it:other_build_options}]

{pstd}{ul:Launch Bokeh Server (blocking — press Ctrl+C to stop)}{p_end}

{p 8 17 2}
{cmd:dash serve}
[{cmd:,}
{cmd:port(}{it:#}{cmd:)}
{cmd:nobrowser}
{cmd:timeout(}{it:#}{cmd:)}]

{pstd}{ul:Clear registry}{p_end}

{p 8 17 2}
{cmd:dash clear}

{pstd}{ul:Setup}{p_end}

{p 8 17 2}
{cmd:dash_setup}

{pstd}
where {it:plot_specs} = {cmd:(}{it:plottype varlist} [{cmd:,} {it:options}]{cmd:)}
[{cmd:(}{it:plottype varlist} [{cmd:,} {it:options}]{cmd:)} ...]
or equivalently using {cmd:||} separators.


{marker description}
{title:Description}

{pstd}
{cmd:dash} accepts the same syntax as {helpb twoway} and produces an
interactive HTML file instead of a static Stata graph window.
The HTML file works offline in any modern browser — no server, internet
connection, or special software is required.

{pstd}
For plot types, marker/line/axis options, and {it:if}/{in} qualifiers,
{cmd:dash} accepts the same syntax as {helpb twoway}.
See {manhelp twoway G-2:graph twoway} for the full reference.

{pstd}
This help file documents only the features that differ from or extend
{cmd:twoway}.


{marker differences}
{title:Differences from twoway}

{phang2}1.  {ul:Output is interactive HTML, not a Stata graph window.}
    Every figure includes pan, zoom, box-select, lasso-select,
    and hover tooltips automatically.
    The file can be shared, emailed, or opened in any browser.

{phang2}2.  {ul:The {cmd:name()} option is repurposed.}
    In {cmd:twoway}, {cmd:name()} stores the graph in Stata's named graph
    memory.  In {cmd:dash}, {cmd:name()} registers the graph specification
    in the dashboard registry for use with {cmd:dash build}.
    It does NOT interact with Stata's graph memory.

{phang2}3.  {ul:New subcommands.}
    {cmd:dash kpi}, {cmd:dash build}, and {cmd:dash clear} have no
    {cmd:twoway} equivalents.  See {help dash##subcommands:Subcommands}.

{phang2}4.  {ul:New build-time options.}
    {cmd:link()}, {cmd:filter()}, {cmd:layout()}, and {cmd:theme()} are
    specific to {cmd:dash} and control multi-graph layout and
    interactivity.

{phang2}5.  {ul:Unsupported twoway options.}
    The following {cmd:twoway} options are not yet supported by {cmd:dash}:
    {cmd:play()}, {cmd:nodraw}.
    Specifying them will produce a warning and the option will be ignored.
    Note: {cmd:scheme()} is fully supported — see
    {help dash##scheme:Stata scheme support} below.

{phang2}6.  {ul:Variable and value labels used automatically.}
    {cmd:dash} reads variable labels (for axis titles) and value labels
    (for categorical tick labels, filter dropdowns, and legend entries)
    without any additional options.


{marker subcommands}
{title:Subcommands}

{dlgtab:dash (plot definition)}

{pstd}
Called without a subcommand keyword, {cmd:dash} parses a plot
specification and either renders it immediately (no {cmd:name()} option)
or stores it in the registry for later use with {cmd:dash build}
(with {cmd:name()}).

{dlgtab:dash kpi}

{pstd}
Computes a scalar statistic and registers a KPI card to be placed in
the dashboard layout alongside graph figures.
See {help dash##kpi:KPI Cards} for details.

{dlgtab:dash build}

{pstd}
Assembles all registered graphs and KPI cards into a dashboard.
With no {cmd:server} option, writes a self-contained standalone HTML file.
With {cmd:server}, writes a Bokeh Server {cmd:.py} application file instead
(requires {cmd:.py} extension on {cmd:saving()}).
See {help dash##dashboard_options:Dashboard Options}.

{dlgtab:dash serve}

{pstd}
Launches a Bokeh Server serving the current registry as a live dashboard.
The server runs in the foreground; Stata is blocked until you press
Ctrl+C or the optional {cmd:timeout()} expires.  Unlike standalone HTML,
the server recalculates aggregated layers (histograms, fitted lines,
kernel density curves) and KPI values from the filtered dataset on every
widget interaction.

{pstd}
{ul:Options:}

{synoptset 20 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmd:port(}{it:#}{cmd:)}}TCP port for the Bokeh Server; must be
    an integer in the range 1024–65535; default 5006{p_end}
{synopt:{cmd:nobrowser}}do not open a browser window automatically{p_end}
{synopt:{cmd:timeout(}{it:#}{cmd:)}}stop the server after {it:#} seconds;
    0 means run until Ctrl+C (default){p_end}
{synoptline}

{dlgtab:dash clear}

{pstd}
Drops all {cmd:$dash_*} global macros, clearing the registry.
Run this before starting a new dashboard definition.


{marker dashboard_options}
{title:Dashboard Options}

{pstd}
The following options are available on {cmd:dash build}.

{synoptset 24 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}}required; path to
    the output HTML file (must end in {cmd:.html}; no {cmd:..}
    traversal allowed){p_end}
{synopt:{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}}dashboard page title{p_end}
{synopt:{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}}dashboard subtitle{p_end}
{synopt:{cmdab:lay:out}{cmd:(}{it:spec}{cmd:)}}grid layout; see
    {help dash##layout:Layout}{p_end}
{synopt:{cmd:link(}{it:names}{cmd:)}}names of graphs to link for brushing;
    see {help dash##linking:Linking and Brushing}{p_end}
{synopt:{cmd:filter(}{it:varname,...}{cmd:)}}add a filter widget;
    see {help dash##filters:Filters}{p_end}
{synopt:{cmd:theme(}{it:name}{cmd:)}}dashboard color theme
    ({cmd:default}, {cmd:clean}, {cmd:dark}){p_end}
{synopt:{cmd:server}}write a self-contained Bokeh Server {cmd:.py} app
    instead of a standalone HTML file; saving() path must end in
    {cmd:.py}; does not block or open a browser{p_end}
{synopt:{cmd:replace}}overwrite output file if it already exists{p_end}
{synoptline}


{marker layout}
{title:Layout}

{pstd}
The {cmd:layout()} option controls how graphs and KPI cards are arranged
in the dashboard grid.

{phang2}{cmd:layout(auto)} — {cmd:dash} chooses a square-ish grid
    automatically based on the number of registered items.  This is
    the default.

{phang2}{cmd:layout(}{it:rows} {it:cols}{cmd:)} — explicit grid dimensions.
    Example: {cmd:layout(2 3)} creates a grid with 2 rows and 3 columns.
    If the number of registered items is less than {it:rows} × {it:cols},
    the remaining cells are left empty.

{phang2}{cmd:layout(}{it:name}{cmd::}{it:row}{cmd:,}{it:col} ...{cmd:)} —
    explicit placement.  Each registered item is placed at the specified
    {it:row},{it:col} position (1-indexed).  Example:
    {cmd:layout(s1:1,1 s2:1,2 k1:2,1)}.


{marker linking}
{title:Linking and Brushing}

{pstd}
Graphs in the same link group share a single Bokeh {cmd:ColumnDataSource}.
Selecting observations in one graph (via box-select or lasso-select)
automatically highlights the same observations in all other linked graphs.

{pstd}
{cmd:link(}{it:name1} {it:name2} [{it:name3} ...]{cmd:)} — link the
specified graphs.  All graphs must have been registered with {cmd:name()}.
Only one link group per dashboard is supported.

{pstd}
{cmd:link(_all)} — link all registered graphs.

{pstd}
Graphs not in the link group receive their own independent data source
and are unaffected by selection in linked graphs.


{marker filters}
{title:Filters}

{pstd}
Each {cmd:filter()} option on {cmd:dash build} adds a widget above the
dashboard that filters observations across all graphs (unless excluded).

{pstd}
Syntax:
{cmd:filter(}{it:varname}{cmd:,}
{cmd:type(}{it:filter_type}{cmd:)}
[{cmd:exclude(}{it:namelist}{cmd:)}]{cmd:)}

{phang2}{cmd:type(dropdown)} — select widget showing unique values of
    {it:varname}.  Value labels are used for display text when available.
    An "All" option removes the filter.

{phang2}{cmd:type(slider)} — slider that filters observations where
    {it:varname} ≥ slider value.

{phang2}{cmd:type(range)} — range slider that filters observations where
    {it:varname} is between the low and high slider values.

{phang2}{cmd:exclude(}{it:namelist}{cmd:)} — prevent the filter from
    affecting the specified graphs and KPIs.

{pstd}
Multiple {cmd:filter()} options may be specified on the same
{cmd:dash build} call.

{pstd}
Example:

{phang2}{cmd:dash build, saving(out.html) }{cmd:///}{p_end}
{phang2}{cmd:    filter(foreign, type(dropdown))}{cmd: ///}{p_end}
{phang2}{cmd:    filter(weight, type(range) exclude(k1))}{p_end}


{marker kpi}
{title:KPI Cards}

{pstd}
KPI cards display a single computed statistic as a styled card widget
in the dashboard layout.  They update automatically when filters or
brush selections change (depending on the {cmd:update()} option).

{pstd}
{ul:Syntax:}
{cmd:dash kpi} {it:stat}{cmd:(}{it:varname}{cmd:)} {ifin} {cmd:,}
{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:nam:e}{cmd:(}{it:id}{cmd:)}
[{it:options}]

{pstd}
{ul:Supported statistics:}

{synoptset 15 tabbed}
{synopthdr:statistic}
{synoptline}
{synopt:{cmd:mean}}arithmetic mean{p_end}
{synopt:{cmd:sum}}sum{p_end}
{synopt:{cmd:count}}number of non-missing observations{p_end}
{synopt:{cmd:dcount}}number of distinct values{p_end}
{synopt:{cmd:min}}minimum value{p_end}
{synopt:{cmd:max}}maximum value{p_end}
{synopt:{cmd:median}}median (50th percentile){p_end}
{synopt:{cmd:sd}}standard deviation{p_end}
{synopt:{cmd:p25}}25th percentile{p_end}
{synopt:{cmd:p50}}50th percentile (same as {cmd:median}){p_end}
{synopt:{cmd:p75}}75th percentile{p_end}
{synoptline}

{pstd}
{ul:Options:}

{synoptset 24 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}}required; label displayed
    above the statistic value{p_end}
{synopt:{cmdab:nam:e}{cmd:(}{it:id}{cmd:)}}required; identifier for
    placement and filter exclusion{p_end}
{synopt:{cmdab:fmt:}{cmd:(}{it:format}{cmd:)}}Stata display format string
    (e.g., {cmd:%9.1f}, {cmd:%12.0fc}){p_end}
{synopt:{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}}smaller label displayed
    below the value{p_end}
{synopt:{cmd:color(}{it:color}{cmd:)}}text color of the value (Stata color
    name or hex){p_end}
{synopt:{cmd:bgcolor(}{it:color}{cmd:)}}background color of the card{p_end}
{synopt:{cmdab:upd:ate}{cmd:(}{it:mode}{cmd:)}}how the KPI reacts to
    user interaction; {it:mode} is {cmd:filter}, {cmd:brush}, or
    {cmd:both} (default: {cmd:filter}){p_end}
{synoptline}

{pstd}
{ul:Update modes:}

{phang2}{cmd:update(filter)} — KPI recalculates when filter widgets
    change.  This is the default.

{phang2}{cmd:update(brush)} — KPI recalculates when observations are
    selected via box-select or lasso-select brushing.

{phang2}{cmd:update(both)} — KPI recalculates on either filter changes
    or brush selections.


{marker server_mode}
{title:Server Mode}

{pstd}
{cmd:dash serve} (and {cmd:dash build, server}) produce a Bokeh Server
application rather than a standalone HTML file.  The two modes differ as
follows:

{synoptset 28 tabbed}
{synopthdr:Feature}
{synoptline}
{synopt:{it:}}                         {it:Standalone HTML}  {it:Bokeh Server}{p_end}
{synopt:Requires internet / server}    No                  Yes (local){p_end}
{synopt:Shareable as a single file}    Yes                 No (.py + bokeh serve){p_end}
{synopt:Filter widgets}                CustomJS (in-browser) Python callbacks{p_end}
{synopt:KPI recomputation on filter}   Yes (JS aggregation) Yes (Python/pandas){p_end}
{synopt:Histogram recompute on filter} No                  Yes{p_end}
{synopt:Fit-line recompute on filter}  No                  Yes{p_end}
{synopt:Brush/lasso KPI update}        Yes                 Yes{p_end}
{synopt:Deployment}                    Email / open file   {cmd:bokeh serve app.py}{p_end}
{synoptline}

{pstd}
{ul:Blocking behavior.}  {cmd:dash serve} blocks Stata until the server
is stopped.  Stop it by pressing Ctrl+C in the Stata console, or set
{cmd:timeout()} to limit the run time automatically.

{pstd}
{ul:Running the generated .py file independently.}
{cmd:dash build, saving(app.py) server} writes a self-contained server app
that embeds all data as base64.  Run it outside Stata with:

{phang2}{cmd:bokeh serve app.py --show}

{pstd}
{ul:Security.}  The Bokeh Server restricts WebSocket connections to
{cmd:localhost} only.  All user-supplied strings (titles, KPI labels) are
HTML-escaped in the generated file.  Data values are base64-encoded,
preventing any data content from affecting the Python file syntax.


{marker examples}
{title:Examples}

{pstd}{ul:Basic single scatter plot}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, saving(scatter.html)}{p_end}

{pstd}{ul:Overlaid scatter + fit line}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash (scatter mpg weight, mc(red)) (lfit mpg weight), ///}{p_end}
{phang2}{cmd:.     title("MPG vs Weight") saving(fit.html)}{p_end}

{pstd}{ul:Multi-graph dashboard with layout}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1) title("MPG vs Weight")}{p_end}
{phang2}{cmd:. dash scatter mpg length, name(s2) title("MPG vs Length")}{p_end}
{phang2}{cmd:. dash histogram mpg, name(h1) title("MPG Distribution")}{p_end}
{phang2}{cmd:. dash build, saving(dashboard.html) layout(2 2) replace}{p_end}

{pstd}{ul:Linked brushing across scatter plots}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash scatter price mpg, name(s2)}{p_end}
{phang2}{cmd:. dash build, saving(linked.html) link(s1 s2) replace}{p_end}

{pstd}{ul:KPI cards with filter}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1) title("MPG vs Weight")}{p_end}
{phang2}{cmd:. dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f) update(filter)}{p_end}
{phang2}{cmd:. dash kpi count(mpg), title("N Obs") name(k2) fmt(%9.0fc) update(filter)}{p_end}
{phang2}{cmd:. dash build, saving(kpi.html) ///}{p_end}
{phang2}{cmd:.     filter(foreign, type(dropdown)) replace}{p_end}

{pstd}{ul:If qualifier}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight if foreign == 1, saving(foreign.html)}{p_end}

{pstd}{ul:Live Bokeh Server (blocking — Ctrl+C to stop)}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1) title("MPG vs Weight")}{p_end}
{phang2}{cmd:. dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f) update(filter)}{p_end}
{phang2}{cmd:. dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace}{p_end}
{phang2}{cmd:. * -- or launch live server (filter recomputes aggregates) --}{p_end}
{phang2}{cmd:. dash serve, port(5006)}{p_end}

{pstd}{ul:Write server app to file (non-blocking)}{p_end}
{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash build, saving(app.py) server replace}{p_end}
{phang2}{cmd:. * Run outside Stata:  bokeh serve app.py --show}{p_end}


{marker faceting}
{title:Faceting with by()}

{pstd}
{cmd:dash} supports Stata's {opt by(varlist)} option for faceted graphs.
Each unique value of {it:varlist} produces a separate panel, filtered to
that group.

{synoptset 30}{...}
{synopt:{opt by(varlist)}}facet graph by unique values of {it:varlist}{p_end}
{synopt:{opt by(varlist, cols(#))}}arrange facet panels in {it:#} columns{p_end}
{synopt:{opt by(varlist, total)}}add a "Total" panel showing all data{p_end}
{synopt:{opt by(varlist, missing)}}include a panel for missing values{p_end}
{synoptline}

{pstd}
Value labels are used for facet panel titles when available.
Multiple by-variables produce composite labels (e.g. "Domestic / 3").
{cmd:by()} cannot be combined with {cmd:link()}.

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, by(foreign)}{p_end}


{marker marker_labels}
{title:Marker Label Options}

{pstd}
Any plot layer that renders individual data points supports marker label
annotations.  These options apply to the per-plot specification (not to
{cmd:dash build} options).

{synoptset 28}{...}
{synopt:{cmdab:mla:bel(}{it:varname}{cmd:)}}annotate each observation with
    the value of {it:varname}; applies to scatter, line, connected, bar,
    spike, dot, dropline, and all range plot types (rspike, rcap, rline,
    rarea, rbar, rcapsym){p_end}
{synopt:{cmdab:mlac:olor(}{it:color}{cmd:)}}color of the label text{p_end}
{synopt:{cmdab:mlas:ize(}{it:size}{cmd:)}}size keyword or number; e.g.
    {cmd:small}, {cmd:medium}, {cmd:large}{p_end}
{synopt:{cmdab:mlap:osition(}{it:#}{cmd:)}}clock position (0–12) for label
    placement relative to the data point; 3 = right (default), 12 = above,
    6 = below, 9 = left{p_end}
{synopt:{cmdab:mlag:ap(}{it:#}{cmd:)}}additional offset in pixels added to
    the clock-position offset{p_end}
{synoptline}

{pstd}
For range plot types, labels are placed at the upper boundary (y2 variable).

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, mlabel(make) mlabcolor(navy) mlabsize(small)}{p_end}


{marker smoother_options}
{title:Smoother Plot-Type Options}

{pstd}
The following plot-level options apply specifically to {cmd:lpoly},
{cmd:lpolyci}, {cmd:fpfit}, and {cmd:fpfitci} plot types.

{synoptset 20}{...}
{synopt:{opt bwidth(#)}}bandwidth for local polynomial smoother ({cmd:lpoly}/
    {cmd:lpolyci}) as a fraction of the x-range; default is 0.5; valid range
    0.01–1.0{p_end}
{synopt:{opt degree(#)}}polynomial degree for local polynomial smoother;
    0 = Nadaraya–Watson kernel estimator (default), 1 = local linear,
    2 = local quadratic{p_end}
{synoptline}

{pstd}
{cmd:lpoly} and {cmd:lpolyci} implement Gaussian kernel-weighted local
polynomial regression — the same smoother underlying Stata's
{helpb twoway lpoly}.  {cmd:lpolyci} adds a bootstrap 95% confidence band.

{pstd}
{cmd:fpfit} and {cmd:fpfitci} implement degree-2 fractional polynomial
fitting (Royston & Altman, 1994), selecting the pair of powers from
{c -(}{cmd:–2}, {cmd:–1}, {cmd:–0.5}, {cmd:0}, {cmd:0.5}, {cmd:1},
{cmd:2}, {cmd:3}{c )-} that minimises the residual sum of squares.
{cmd:fpfitci} adds a bootstrap 95% confidence band.  Both require
positive x values.

{pstd}
{it:Example:}
{phang2}{cmd:. dash (scatter mpg weight) (lpoly mpg weight, bwidth(0.4)), saving(lp.html)}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (fpfit mpg weight), saving(fp.html)}{p_end}


{marker region_options}
{title:Region Styling Options}

{pstd}
{cmd:dash} supports the standard Stata {helpb twoway} region-styling options
for controlling the background colors of the inner plot area and the outer
graph border.

{synoptset 35}{...}
{synopt:{opt plotregion(color(}{it:color}{opt ))}}background color of the
    inner plot canvas; Bokeh {cmd:background_fill_color}{p_end}
{synopt:{opt plotregion(lcolor(}{it:color}{opt ))}}border line color
    of the inner plot area; Bokeh {cmd:outline_line_color}{p_end}
{synopt:{opt plotregion(lwidth(}{it:#}{opt ))}}border line width
    of the inner plot area{p_end}
{synopt:{opt graphregion(color(}{it:color}{opt ))}}background color of the
    outer margin area; Bokeh {cmd:border_fill_color}{p_end}
{synopt:{opt graphregion(fcolor(}{it:color}{opt ))}}fill color alias for
    {cmd:graphregion(color())}{p_end}
{synoptline}

{pstd}
Colors may be any Stata named color ({cmd:navy}, {cmd:maroon},
{cmd:forest_green}, etc.), an RGB triplet ({cmd:"255 0 0"}),
or a hex string ({cmd:#1a476f}).

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, plotregion(color(ltblue)) graphregion(color(white))}{p_end}

{pstd}
Abbreviations: {cmd:plotr()} for {cmd:plotregion()},
{cmd:graphr()} for {cmd:graphregion()}.


{marker axis_options}
{title:Axis and Display Options}

{pstd}
The following graph-level options control axis titles, custom tick labels,
annotations, reference lines, axis scaling, and figure proportions.
All are specified in the per-graph option list (after the comma following
the plot specification).

{synoptset 38}{...}
{synopt:{cmdab:xti:tle(}{it:string}{cmd:)}}label for the x axis{p_end}
{synopt:{cmdab:yti:tle(}{it:string}{cmd:)}}label for the y axis{p_end}
{synopt:{cmdab:xla:bel(}{it:#}[{it:#} ...]{cmd:)}}custom x-axis tick positions{p_end}
{synopt:{cmdab:yla:bel(}{it:#}[{it:#} ...]{cmd:)}}custom y-axis tick positions{p_end}
{synopt:{cmdab:xlab:el(}{it:#}[{it:#} ...]{cmd:, format(}{it:fmt}{cmd:))}}custom ticks with format string{p_end}
{synopt:{cmdab:xsc:ale(log)}}display the x axis on a log scale{p_end}
{synopt:{cmdab:ysc:ale(log)}}display the y axis on a log scale{p_end}
{synopt:{cmdab:xli:ne(}{it:#}[{it:#} ...]{cmd:)}}draw vertical reference lines at x = {it:#}{p_end}
{synopt:{cmdab:yli:ne(}{it:#}[{it:#} ...]{cmd:)}}draw horizontal reference lines at y = {it:#}{p_end}
{synopt:{cmdab:no:te(}{it:string}{cmd:)}}footnote text below the figure{p_end}
{synopt:{cmdab:cap:tion(}{it:string}{cmd:)}}caption text below the figure{p_end}
{synopt:{cmdab:asp:ectratio(}{it:#}{cmd:)}}height-to-width ratio of the plot area
    (e.g. {cmd:aspectratio(1)} for a square plot){p_end}
{synoptline}

{pstd}
{it:Examples:}
{phang2}{cmd:. dash scatter mpg weight, xtitle(Weight (lbs)) ytitle(Mileage)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xscale(log) yscale(log)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xline(3000) yline(20 30)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(1000 2000 3000 4000) ylabel(10 20 30 40)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, note(Source: 1978 Automobile Data)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, aspectratio(0.75)}{p_end}


{marker unsupported}
{title:Unsupported Stata twoway options}

{pstd}
The following Stata {helpb twoway} options are either silently ignored or not
supported.  No error is produced for unknown options, so existing Stata graph
commands copy-pasted into {cmd:dash} will still run even when they contain
options that have no Bokeh equivalent.

{phang2}{opt connect(list)} — control how missing values join points.
    Not applicable to Bokeh renderers; use {cmd:connected} plot type instead.
    Silently ignored when encountered.

{phang2}{opt cmissing(y|n ...)} — treatment of missing values in lines.
    Bokeh always drops missing observations before rendering.
    Silently ignored when encountered.

{phang2}{opt jitter(#)} — add random noise to marker positions.
    Uniformly distributed noise scaled to #% of the axis range is added to
    both x and y coordinates.  Combine with {opt jseed(#)} for reproducible
    results.  Supported on {cmd:scatter}, {cmd:dot}, {cmd:dropline}, and
    {cmd:scatteri} plot types; silently ignored on line and fit plots.

{phang2}{opt jseed(#)} — random-number seed for {opt jitter()}.
    Pass any non-negative integer to make jitter reproducible across renders.

{phang2}{opt msangle(#)} — angle of asymmetric marker symbols.
    Bokeh's {cmd:scatter} glyph does not support per-marker rotation.
    Silently ignored when encountered.

{phang2}{opt recast(plottype)} — recast one plot type to another at render time.
    Not supported; specify the desired plot type directly.
    Silently ignored when encountered.

{phang2}{opt xaxis(#)} / {opt yaxis(#)} — assign a plot layer to a secondary axis.
    Use {cmd:yaxis(2)} on any plot layer to add a right-hand y-axis scaled to
    that layer's data.  Use {cmd:xaxis(2)} to add a top x-axis.  The secondary
    axis range is computed automatically from the data.  Pair with
    {cmd:ytitle2()}, {cmd:ylabel2()}, {cmd:yscale2(log)} for the right-hand
    axis (or {cmd:xtitle2()}, {cmd:xlabel2()}, {cmd:xscale2(log)} for the
    top axis).

{phang2}{opt scheme(schemename)} — apply a named Stata graph scheme to the dashboard.
    {cmd:dash} ships with bundled approximations of five built-in Stata schemes:
    {cmd:s2color} (default), {cmd:s1color}, {cmd:s1mono}, {cmd:economist}, and
    {cmd:sj}.  To use a custom scheme, place a Stata-format {cmd:.scheme} file
    in the current working directory and specify its base name without the
    extension.  The scheme controls background colors, marker color cycles,
    line patterns, font sizes, and grid appearance.  Explicit graph options
    ({cmd:bgcolor()}, {cmd:plotbgcolor()}, etc.) take precedence over scheme
    defaults.

{phang2}{opt nodraw} — suppress graph display.
    Not applicable; {cmd:dash} always writes to a file or starts a server.
    Use the {opt saving()} option without immediately opening the output.


{marker dependencies}
{title:Dependencies}

{pstd}
Run {helpb dash_setup} once before using {cmd:dash}.
{cmd:dash_setup} installs and verifies all required software:

{phang2}{ul:Python 3.8+} — linked to Stata via {helpb python}.

{phang2}{ul:Python packages} — bokeh≥3.0, numpy≥1.23, scipy≥1.9,
    statsmodels≥0.13, pandas≥1.5.

{phang2}{ul:jsonio} — Stata package for JSON serialization of datasets.
    See {helpb jsonio}.


{marker author}
{title:Also see}

{psee}
{helpb dash_setup}, {helpb twoway}, {helpb jsonio}, {helpb python}
