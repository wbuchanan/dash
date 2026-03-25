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

{pstd}{ul:Build dashboard}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}
[{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}
{cmdab:lay:out}{cmd:(}{it:layout_spec}{cmd:)}
{cmd:link(}{it:namelist} | {cmd:_all}{cmd:)}
{cmd:filter(}{it:varname}{cmd:, type(}{it:filter_type}{cmd:)} [{cmd:exclude(}{it:namelist}{cmd:)}]{cmd:)}
{cmd:theme(}{it:theme_name}{cmd:)}
{cmd:replace}]

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
    {cmd:scheme()}, {cmd:play()}, {cmd:nodraw}.
    Specifying them will produce a warning and the option will be ignored.

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
Assembles all registered graphs and KPI cards into a single HTML
dashboard file.  See {help dash##dashboard_options:Dashboard Options}.

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
