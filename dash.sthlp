{smcl}
{* *! version 2.0  27mar2026}{...}
{viewerjumpto "Syntax"            "dash##syntax"}{...}
{viewerjumpto "Description"       "dash##description"}{...}
{viewerjumpto "Differences from twoway" "dash##differences"}{...}
{viewerjumpto "Subcommands"       "dash##subcommands"}{...}
{viewerjumpto "Dashboard Options" "dash##dashboard_options"}{...}
{viewerjumpto "Layout"            "dash##layout"}{...}
{viewerjumpto "Linking and Brushing" "dash##linking"}{...}
{viewerjumpto "The toolbar"       "dash##toolbar"}{...}
{viewerjumpto "Filters"           "dash##filters"}{...}
{viewerjumpto "KPI Cards"         "dash##kpi"}{...}
{viewerjumpto "Server Mode"       "dash##server_mode"}{...}
{viewerjumpto "Resource limits"   "dash##limits"}{...}
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
{cmd:dash} {it:plot_specs} {ifin} {weight} [{cmd:,} {it:graph_options}
{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}]

{pstd}{ul:Named graph (accumulate for multi-graph dashboard)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} {weight} [{cmd:,} {it:graph_options}
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
{cmd:filter(}{it:varname}{cmd:, type(}{it:filter_type}{cmd:)} [{cmd:exclude(}{it:namelist}{cmd:)} {cmd:label(}{it:string}{cmd:)}]{cmd:)}
{cmd:tabs(}{it:tab_spec}{cmd:)}
{cmdab:filterpos:ition}{cmd:(top}|{cmd:left)}
{cmd:theme(}{it:theme_name}{cmd:)}
{cmdab:sch:eme}{cmd:(}{it:schemename}{cmd:)}
{cmdab:nobr:owser}
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
{cmd:timeout(}{it:#}{cmd:)}
[{it:other_build_options}]]

{pstd}{ul:Clear registry}{p_end}

{p 8 17 2}
{cmd:dash clear}

{pstd}{ul:Setup}{p_end}

{p 8 17 2}
{cmd:dash_setup}

{pstd}
where {it:plot_specs} = {cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)}
[{cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)} ...]
or equivalently using {cmd:||} separators.  A {it:weight} is one
variable, {cmd:[aweight=}{it:varname}{cmd:]}; see
{help dash##weights:Weights}.


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
    Every figure includes pan, zoom, box-select, lasso-select, undo, redo,
    reset, a button that saves the figures as a PNG image, and hover
    tooltips, automatically; see {help dash##toolbar:The toolbar}.
    The file can be shared, emailed, or opened in any browser.

{phang2}2.  {ul:The {cmd:name()} option is repurposed.}
    In {cmd:twoway}, {cmd:name()} stores the graph in Stata's named graph
    memory.  In {cmd:dash}, {cmd:name()} registers the graph specification
    in the dashboard registry for use with {cmd:dash build}.
    It does NOT interact with Stata's graph memory.  A named graph is
    written by {cmd:dash build}; {cmd:saving()} on a named graph is
    accepted, named in the note, and writes nothing.

{phang2}    {ul:Graphs and KPI cards share one namespace.}  A name holds one
    item, whichever kind it is, so {cmd:dash kpi} cannot quietly take a name
    a graph already holds and a graph cannot take a KPI's.  Either is
    refused with {cmd:r(198)} unless you write
    {cmd:name(}{it:name}{cmd:, replace)}, which retires whatever held the
    name before.  {cmd:dash clear} empties the registry.

{phang2}    {ul:What a name may be.}  A name starts with a letter or an
    underscore and holds only letters, digits and underscores: at most 22
    characters for a graph and 18 for a KPI card.  {cmd:dash} keeps each
    item in Stata globals named after it: a graph in
    {cmd:$dash_json_}{it:name} and {cmd:$dash_spec_}{it:name}, a KPI card
    in {cmd:$dash_kpi_}{it:name} and in one global for each of its fields,
    {cmd:$dash_kpi_}{it:name}{cmd:__}{it:field}, a field being at most three
    letters (the card's statistic is {cmd:$dash_kpi_}{it:name}{cmd:__sta}).
    A global's name is at most 32 characters, which is what sets the two
    limits.  A name may not hold two underscores in a row: {cmd:dash}
    names what it generates with them -- the panels of a {cmd:by()} graph
    {cmd:g1} are {cmd:g1__by__0}, {cmd:g1__by__1}, ... -- and a name of
    that form would take one of their places; they also separate a KPI
    card's name from its fields, so that no name reaches the globals of
    another item.  Such a name is refused with {cmd:r(198)}.  So is
    {cmd:_all}, the word {cmd:link(_all)} uses for every graph.  The
    registry holds at most 100 items; see
    {help dash##limits:Resource limits}.

{phang2}    {ul:The registry lives in Stata globals.}  It is kept in
    {cmd:$dash_graph_registry} and a set of {cmd:$dash_*} macros, which is
    what lets {cmd:dash clear} empty it and what lets a later
    {cmd:dash serve} inherit a {cmd:dash build}'s options.  Setting those
    macros by hand is not supported: {cmd:dash} validates what it registers,
    not what you assign afterwards.

{phang2}3.  {ul:New subcommands.}
    {cmd:dash kpi}, {cmd:dash build}, and {cmd:dash clear} have no
    {cmd:twoway} equivalents.  See {help dash##subcommands:Subcommands}.

{phang2}    {ul:Where a graph-level option may be written.}  A
    graph-level option such as {cmd:title()} is honoured wherever
    {cmd:twoway} honours it: after the top-level comma, or inside a plot
    segment, in both the parenthesis and the {cmd:||} forms.

{phang3}{cmd:. dash (scatter mpg weight) (line mpg weight), title("G") name(g1)}{p_end}
{phang3}{cmd:. dash (scatter mpg weight, title("A")) (line mpg weight), name(g2)}{p_end}

{phang2}    Both register a titled graph.  When more than one place names the
    same option, {cmd:dash} resolves it as {cmd:twoway} does: an option
    written after the top-level comma beats one written inside a segment,
    and among segments the last one to name it wins -- including when the
    last one gives an empty value, which clears it.

{phang2}4.  {ul:New build-time options.}
    {cmd:link()}, {cmd:filter()}, {cmd:layout()}, and {cmd:theme()} are
    specific to {cmd:dash} and control multi-graph layout and
    interactivity.

{phang2}5.  {ul:Unsupported twoway options.}
    {cmd:dash} accepts every {cmd:twoway} option.  An unknown option is never
    an error, so a command copy-pasted from a do-file always runs.  Anything
    {cmd:dash} cannot honour is named once per command, in a single note:

{p 12 12 2}{cmd:. dash scatter mpg weight, play(x) text(20 3000 "hi")}{p_end}
{p 12 12 2}{cmd:dash: ignoring unsupported option(s): play() text()}{p_end}

{phang2}
    The note names option {it:names}, never the values supplied.  Because
    an unknown option cannot be distinguished from a misspelled supported
    one, a typo is reported as ignored rather than rejected: {cmd:titl(x)}
    is abbreviated {cmd:title()} and works, but {cmd:titel(x)} appears in
    the note.  Nothing is ever dropped without being named.  The full list
    is in {help dash##unsupported:Unsupported Stata twoway options}.
    The same holds one level down: a sub-option of {cmd:legend()},
    {cmd:xlabel()}/{cmd:ylabel()}, {cmd:xscale()}/{cmd:yscale()},
    {cmd:xtitle()}/{cmd:ytitle()}, {cmd:title()}, {cmd:subtitle()},
    {cmd:note()}, {cmd:caption()}, {cmd:xline()}/{cmd:yline()} or
    {cmd:filter()} that {cmd:dash} does not implement is named in a
    warning, as {cmd:by()}'s are:
    {cmd:dash: legend() sub-option(s) not implemented and ignored: span stack}.
    A weight, {cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=]} or
    {cmd:[pweight=]}, is honoured on the statistical layers that take it
    in {cmd:twoway} and refused, as {cmd:twoway} refuses it, where they do
    not; on {cmd:scatter} and the other glyph layers it is named in the
    same note by type and never by variable, as {cmd:[aweight]}.  See
    {help dash##weights:Weights}.
    Note: {cmd:scheme()} is fully supported — see
    {help dash##scheme:Stata scheme support} below.

{marker validation}
{phang2}    {ul:Option values.}  A value is refused where {cmd:twoway}
    refuses it, and a word is refused where a number-only option was given
    one that {cmd:twoway} would have swallowed in silence.  A style name
    that {cmd:dash} does not recognise (a colour, a marker symbol, a size,
    a line width, a line pattern, an angle, a clock position or a fill
    intensity) is reported once per render and the scheme's default drawn,
    as {cmd:twoway} does with its own "named style not found" note.  A
    refusal is one line naming the option and the value, printed before
    any Python runs, with r(198), or r(111) for a variable that does not
    exist:

{phang3}{cmd:. dash (scatter mpg weight, yaxis(3))}{p_end}
{phang3}{cmd:dash: yaxis() must be an integer between 1 and 2 (got: 3). dash draws two axes.}{p_end}

{phang2}    The bounds checked in Stata.  Numbers: {cmd:jitter()} 0 to 100;
    {cmd:malpha()}, {cmd:lalpha()} and {cmd:falpha()} 0 to 100;
    {cmd:level()} strictly between 0 and 100; {cmd:aspectratio()} 0 or
    more; {cmd:base()} and {cmd:start()} any number; {cmd:barwidth()},
    {cmd:width()} and {cmd:bwidth()} positive, and on {cmd:lowess}
    {cmd:bwidth()} is a fraction of the sample, so at most 1.  Integers:
    {cmd:yaxis()} and {cmd:xaxis()} 1 or 2; {cmd:degree()} 0 to 3;
    {cmd:n()} 2 to 10000, or 1 to 300 on {cmd:mspline}; {cmd:bin()} 1
    to 1000; {cmd:bands()} 1 to 200;
    {cmd:colornlevels()} 2 to 256; {cmd:jitterseed()} and {cmd:jseed()}
    0 or more; an integer written as {cmd:yaxis(2.0)}, {cmd:yaxis(02)},
    {cmd:yaxis(+2)} or {cmd:n(1E3)} reaches the renderer as 2, 2, 2 and
    1000.  A name or a number: {cmd:msize()}, {cmd:mlabsize()},
    {cmd:mlabgap()}, {cmd:mlabposition()} and {cmd:fintensity()} any
    number; {cmd:lwidth()} and {cmd:mlwidth()} 0 to 10000;
    {cmd:msangle()} -360 to 360; {cmd:xsize()} and {cmd:ysize()} 1 to
    100; a word that only looks like a number, such as
    {cmd:msize(1e400)}, is refused as {cmd:twoway} refuses it.  A word
    from a list, matched without regard to case: {cmd:kernel()},
    {cmd:colpalette()} and {cmd:theme()}.  A scheme name:
    {cmd:scheme()} must be a shipped scheme, a {cmd:theme()} name or a
    {cmd:.scheme} file in the working directory, given by bare name or
    with the extension, wherever it is written (see
    {help dash##scheme:Stata scheme support}).  A list of numbers,
    written as any Stata
    {it:numlist}: {cmd:colorcuts()} one or more, {cmd:range()} exactly
    two; {cmd:colorcuts(1(1)5)} reaches the renderer as 1 2 3 4 5.
    Variables: {cmd:mlabel()} and {cmd:colorvar()} name one, {cmd:hover()}
    one or more, and {cmd:by()} one or more before its comma; each is
    expanded as {cmd:twoway} expands it, so {cmd:by(for)} means
    {cmd:by(foreign)}; a variable that does not exist is r(111), and a
    time-series expression such as {cmd:mlabel(L.mpg)}, which
    {cmd:twoway} draws and {cmd:dash} cannot, is refused.  {cmd:xsize()},
    {cmd:ysize()}, {cmd:aspectratio()}, {cmd:hover()} and {cmd:by()} are
    checked wherever they are written, inside a layer's parentheses or
    after the graph's comma.

{phang2}    Some of those bounds are {cmd:dash}'s own: {cmd:twoway} accepts
    the value, and {cmd:dash} refuses it because it could not draw it.
    Five say so in a second sentence of the message: {cmd:yaxis()} and
    {cmd:xaxis()} 1 or 2 ({cmd:dash} draws two axes; {cmd:twoway} allows
    nine), {cmd:degree()} 0 to 3, {cmd:bin()} up to 1000, {cmd:n()} 2 to
    10000 (on {cmd:mspline}, 1 to 300 is {cmd:twoway}'s own bound), and
    the {cmd:lowess} {cmd:bwidth()} fraction.  The others carry
    no second sentence: {cmd:colornlevels()} 2 to 256, {cmd:jitter()} 0 to
    100, {cmd:level()} strictly inside 0 and 100, {cmd:barwidth()}
    positive, {cmd:aspectratio()} 0 or more, {cmd:jitterseed()} and
    {cmd:jseed()} 0 or more, {cmd:kdensity} {cmd:bwidth()} positive
    ({cmd:kdensity} itself accepts {cmd:bwidth(0)}).  {cmd:bands()} 1 to
    200 is {cmd:twoway}'s own bound ({cmd:bands must be between 1 and
    200}).  Two values {cmd:twoway} refuses,
    {cmd:dash} accepts: {cmd:kernel(GAUSSIAN)} is read as
    {cmd:kernel(gaussian)}, and {cmd:lwidth(())} passes as a name that
    the renderer then reports.  And {cmd:scheme()} and {cmd:theme()}
    are refused where {cmd:twoway} draws {cmd:s2color} with a note,
    because a saved dashboard in the wrong scheme is not a note you
    see; {help dash##scheme:Stata scheme support} says more.

{phang2}    A switch that belongs to one plot type is refused on every
    other, as {cmd:twoway} refuses it, with r(198): {cmd:discrete} on
    {cmd:histogram}; {cmd:stdp}, {cmd:stdf} and {cmd:stdr} on
    {cmd:lfitci} and {cmd:qfitci}; {cmd:mean}, {cmd:noweight},
    {cmd:adjust} and {cmd:logit} on {cmd:lowess}.  Two of {cmd:stdp},
    {cmd:stdf} and {cmd:stdr} together ({cmd:may not combine}) and
    {cmd:discrete} with {cmd:bin()} are refused the same way.  A weight
    the plot type does not take is r(101), as in {cmd:twoway}; see
    {help dash##weights:Weights}.

{phang3}{cmd:. dash (scatter mpg weight, discrete)}{p_end}
{phang3}{cmd:option discrete not allowed}{p_end}

{phang2}    Colours, {cmd:msymbol()}, {cmd:lpattern()}, {cmd:scheme()} and
    the sub-options of the structured options are not checked in Stata.
    An unknown style inside one ({cmd:title(T, size(bogus))}) gets a note
    and the default in {cmd:twoway} and in {cmd:dash} alike; an unknown
    sub-option word, which {cmd:twoway} refuses ({cmd:legend(garbage)},
    {cmd:xscale(bogus)}: r(198)), {cmd:dash} names in its sub-option note
    and draws without.

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
    an integer in the range 1024–65535, written in digits only (no sign,
    decimal point or exponent); default 5006{p_end}
{synopt:{cmd:nobrowser}}do not open a browser window automatically.  The
    rule is {cmd:dash build}'s: a registered graph's {cmd:nodraw} has the
    same effect, and so does setting the global {cmd:$dash_nobrowser}, which
    keeps every {cmd:dash} window shut for the session{p_end}
{synopt:{cmd:timeout(}{it:#}{cmd:)}}stop the server after {it:#} minutes,
    at most nine digits; 0 means run until Ctrl+C (default){p_end}
{synoptline}

{pstd}
{cmd:dash serve} also accepts every option {cmd:dash build} accepts —
{cmd:title()}, {cmd:subtitle()}, {cmd:layout()}, {cmd:link()},
{cmd:filter()}, {cmd:theme()}, {cmd:scheme()}, {cmd:tabs()},
{cmd:filterposition()} and {cmd:csv} — with the same meanings and the same
validation.
See {help dash##dashboard_options:Dashboard Options}.

{pstd}
{ul:Inheriting a previous build.}  If a {cmd:dash build} has already run in
this session, {cmd:dash serve} reuses its options for anything you do not
restate, so

{phang2}{cmd:. dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace}{p_end}
{phang2}{cmd:. dash serve, port(5006)}{p_end}

{pstd}
serves the dashboard you just built, filter and all.  An option given on
{cmd:dash serve} always wins over the inherited one.  {cmd:dash clear}
discards the remembered options along with the registry.

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
{synopt:{cmd:tabs(}{it:tab_spec}{cmd:)}}group graphs and KPI cards into
    tabs; see {help dash##tabs:Tabs}{p_end}
{synopt:{cmdab:filterpos:ition}{cmd:(}{it:where}{cmd:)}}where the filter
    widgets are placed: {cmd:top} (the default) puts them in a row above the
    dashboard, {cmd:left} puts them in a sidebar beside it{p_end}
{synopt:{cmd:csv}}add a {bf:Download CSV} button that downloads the rows
    the filters leave; see {help dash##export:Exporting}{p_end}
{synopt:{cmdab:sch:eme}{cmd:(}{it:schemename}{cmd:)}}apply a named Stata
    graph scheme; see {help dash##scheme:Stata scheme support}{p_end}
{synopt:{cmd:theme(}{it:name}{cmd:)}}an alias for a scheme
    ({cmd:default}, {cmd:clean}, {cmd:mono}, {cmd:dark}, {cmd:economist},
    {cmd:sj}); {cmd:scheme()} wins if both are given{p_end}
{synopt:{cmd:server}}write a self-contained Bokeh Server {cmd:.py} app
    instead of a standalone HTML file; saving() path must end in
    {cmd:.py}; does not block or open a browser{p_end}
{synopt:{cmdab:nobr:owser}}write the dashboard but do not open it in a
    browser.  Stata's own {cmd:nodraw} on the graph has the same effect, and
    setting the global {cmd:$dash_nobrowser} to any non-empty value suppresses
    the window for a whole session -- for {cmd:dash build}, the one-line
    form and {cmd:dash serve} alike -- useful in batch, where one window per
    {cmd:dash build} is rarely wanted{p_end}
{synopt:{cmd:replace}}overwrite output file if it already exists{p_end}
{synoptline}


{marker export}
{title:Exporting}

{pstd}
Every dashboard can save its figures as a PNG image, with the save button
on the toolbar (see {help dash##toolbar:The toolbar}).  With {cmd:csv} it
can also give you its data.

{pstd}
With {cmd:csv}, the dashboard carries a {bf:Download CSV} button beside its
filters (or on its own, when there are none).  It downloads
{it:dashboard.csv}: every observation the filters currently leave, with every
variable the dashboard uses, in the order of the data.  Only the filters
count; a selection brushed on a graph and a graph's own {cmd:if} or {cmd:in}
do not.  A filter at its full extent -- a range spanning every value, a
slider at its minimum -- restricts nothing, as {bf:All} does in a dropdown.
Once moved, a range or slider filter drops observations whose value is
missing, as {cmd:if} {it:x} {cmd:>=} {it:value} does in {cmd:dash}.

{pstd}
The file is written as Stata's {cmd:export delimited} writes one, with these
differences: a date is written in ISO 8601 ({cmd:2020-01-16}; for {cmd:%tc},
{cmd:2020-01-15 13:45:30.25}; for {cmd:%ty}, the year; for {cmd:%tw},
{cmd:%tm}, {cmd:%tq} and {cmd:%th}, the first day of the period); a number is
written in full, with a leading zero ({cmd:0.5}); a text value that begins
with {cmd:=}, {cmd:+}, {cmd:-}, {cmd:@}, a tab or a carriage return is written
after an apostrophe, so that a spreadsheet shows it rather than runs it as a
formula; and the file is UTF-8 with a byte-order mark, which Excel needs and
{cmd:import delimited} reads through.  A value-labelled variable is written as
its labels, as {cmd:export delimited} writes it by default.

{pstd}
{cmd:csv} is off unless asked for, because it lets anyone who opens the
dashboard download every row of every variable it uses -- including one that
only a KPI card summarises.  A saved dashboard with filters already contains
those rows (the filters need them), but a served one sends the browser only
what it draws.  When served, each click is computed on the server from the
same filters, and a session may download twice at once and then once every
five seconds.  {cmd:dash serve} inherits {cmd:csv} from the preceding
{cmd:dash build}, as it inherits every dashboard option.


{marker layout}
{title:Layout}

{pstd}
The {cmd:layout()} option controls how graphs and KPI cards are arranged
in the dashboard grid.

{phang2}{cmd:layout(auto)} — {cmd:dash} chooses a square-ish grid
    automatically based on the number of registered items.  This is
    the default.  Items fill the grid in the order they were registered,
    graphs and KPI cards alike, in both render modes.

{phang2}{cmd:layout(}{it:rows} {it:cols}{cmd:)} — explicit grid dimensions.
    Example: {cmd:layout(2 3)} creates a grid with 2 rows and 3 columns.
    If the number of registered items is less than {it:rows} × {it:cols},
    the remaining cells are left empty.  A grid may have at most as many
    cells as a dashboard may hold graphs and KPI cards ({cmd:$dash_max_graphs},
    default 100; see {help dash##limits:Limits}); a larger one is refused
    with {cmd:r(198)}, because every empty cell is drawn.

{phang2}{cmd:layout(}{it:name}{cmd::}{it:row}{cmd:,}{it:col} ...{cmd:)} —
    explicit placement.  Each registered item is placed at the specified
    {it:row},{it:col} position (1-indexed).  Example:
    {cmd:layout(s1:1,1 s2:1,2 k1:2,1)}.  The largest row times the largest
    column is held to the same limit as a {it:rows} {it:cols} grid.  Every
    name must be a registered graph or KPI card, as in {cmd:link()}.

{phang2}{cmd:layout(bs}[{cmd::} {it:name}{cmd:=}{it:span} ...]{cmd:)} —
    a Bootstrap-style 12-column grid.  With no specification {cmd:dash}
    chooses the spans; otherwise each named item takes the given number of
    columns out of 12, and {cmd:/} starts a new row.  A row whose spans add
    up to more than 12 wraps onto the next line, and a registered item the
    specification does not name is drawn below the rows it gives, the full
    width.  Each name must be registered, and each {it:span} a whole number
    from 1 to 12; a name written without one takes 6.  Example:
    {cmd:layout(bs: k1=3 k2=3 s1=6)}.  A value that reads as placements is
    placements, whatever its first letters: {cmd:layout(bsales:1,1 g2:1,2)}
    places a graph named {cmd:bsales}.  A saved dashboard's grid reflows as
    the browser window narrows: below 992 pixels an item of 4 columns or
    fewer takes half the row, and below 768 every item takes the whole row.
    {cmd:dash serve} and {cmd:dash build, server} draw the same rows and
    spans on a grid that narrows with the window but does not reflow.

{pstd}
A {cmd:layout()} that is not one of these forms as a whole, that names an
item the registry does not hold, that places an item more than once, or that
gives a span outside 1 to 12 is refused with {cmd:r(198)}; nothing is drawn
some other way in silence.


{marker tabs}
{title:Tabs}

{pstd}
{cmd:tabs()} groups registered graphs and KPI cards into named tabs.  The
specification is one or more groups separated by {cmd:/}, each written as a
title, a colon, and the names that belong to it:

{phang2}{cmd:tabs(}{it:title}{cmd::} {it:name} [{it:name} ...]
    [{cmd:/} {it:title}{cmd::} {it:name} ...]{cmd:)}{p_end}

{pstd}
For example:

{phang2}{cmd:dash build, saving(d.html) tabs(Overview: k1 s1 / Detail: s2 s3)}{p_end}

{pstd}
Tab titles are used exactly as written.  A registered item named in no tab is
still drawn, below the tabs.  Names that are not in the registry are ignored.
{cmd:tabs()} works with every {cmd:layout()}.  At most 50 tabs are drawn; a
note names the rest (see {help dash##limits:Resource limits}).


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
{cmd:link(_all)} — link all registered graphs.  {cmd:_all} stands alone:
beside other names it is refused with {cmd:r(198)}, and no graph may be
named {cmd:_all}.

{pstd}
Graphs not in the link group receive their own independent data source
and are unaffected by selection in linked graphs.


{marker toolbar}
{title:The toolbar}

{pstd}
Every figure carries the same tools, in both render modes:

{synoptset 16 tabbed}
{synopthdr:tool}
{synoptline}
{synopt:Pan}drag to move the figure.  This is what a drag does when the
    page opens.{p_end}
{synopt:Wheel zoom}zoom with the mouse wheel or trackpad.  It is off when
    the page opens, so the wheel scrolls the page; click its button to turn
    it on.{p_end}
{synopt:Box zoom}drag a rectangle to zoom to it.{p_end}
{synopt:Box select}drag a rectangle to select the observations inside
    it; see {help dash##linking:Linking and Brushing}.{p_end}
{synopt:Lasso select}draw around observations to select them.{p_end}
{synopt:Undo}step back through your pans and zooms.{p_end}
{synopt:Redo}step forward again.{p_end}
{synopt:Reset}return to the view the page opened with, and clear the
    selection.{p_end}
{synopt:Save}write the figures to a PNG image; see below.{p_end}
{synoptline}

{pstd}
A figure with tooltips also has a hover button, which turns them off and
on.  There is no crosshair tool: in a toolbar that a grid of figures
shares it would draw its lines across every figure at once, and the
tooltip already reads values off a figure.

{pstd}
{ul:One toolbar per grid.}  The figures of a grid share one toolbar, above
the grid.  Choosing a tool there chooses it for every figure in the grid,
and undo, redo and reset act on all of them at once.  Each tab of
{cmd:tabs()} is a grid with a toolbar of its own, and the panels of a
{cmd:by()} graph have one of their own as well.  {cmd:layout(bs)} places
each graph on its own, with its own toolbar beside it, or above the panels
of a {cmd:by()} graph; a graph in a tab is still part of that tab's grid.

{pstd}
{ul:Saving an image.}  The save button writes everything its toolbar
serves as one PNG file.  A grid -- the dashboard's, a tab's, or a
{cmd:by()} graph's panels -- is saved as {cmd:dashboard.png}.  A graph that
{cmd:layout(bs)} places on its own, with its {cmd:by()} panels if it has
any, is saved under its name: {cmd:g1.png} for the graph registered as
{cmd:g1}.  Your browser decides where the file goes.  The image holds only
the figures: a KPI card in a grid is left blank, and the title, the filters
and the tab strip, which sit outside every grid, are not in it.


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
    An "All" option removes the filter.  A dropdown lists at most 1,000
    values: over that, a numeric or date variable is drawn as
    {cmd:type(range)} instead, and a string variable lists its first 1,000
    values in sort order, each with a note (see
    {help dash##limits:Resource limits}).

{phang2}{cmd:type(slider)} — slider that filters observations where
    {it:varname} ≥ slider value.

{phang2}{cmd:type(range)} — range slider that filters observations where
    {it:varname} is between the low and high slider values.

{phang2}{cmd:exclude(}{it:namelist}{cmd:)} — prevent the filter from
    affecting the specified graphs and KPIs.  Excluding a {cmd:by()} graph
    excludes every one of its panels.

{phang2}{cmd:label(}{it:string}{cmd:)} — the text shown beside the widget.
    Without it the variable's own label is used, and failing that its name.
    The text may be anything but a semicolon, which separates filters.

{pstd}
{cmd:type()} must be one of the three above; any other value is named in a
warning and no widget is built.  A group whose variable is not in the data,
or whose {cmd:exclude()} names are not valid names, is refused with the
same kind of warning.  Any other sub-option is accepted, named in a
warning, and ignored.

{pstd}
{ul:More than one filter.}  Give {cmd:filter()} as many times as you need, up
to 20, on the same {cmd:dash build} or {cmd:dash serve} call.  Because Stata's
{cmd:syntax} keeps only the last of a repeated option, {cmd:dash} collects
them itself before parsing and joins them with a semicolon internally; you
never write the semicolon.  Each group is validated on its own, so
{cmd:exclude()} on the second filter is honoured exactly as on the first.

{pstd}
{ul:The dropdown's "All" entry.}  A {cmd:type(dropdown)} widget carries an
{cmd:All} entry that removes the filter.  It is the selected entry when the
dashboard opens, and it is carried in the page as the reserved value
{cmd:__all__}; a variable whose own data contains that string is filtered on
as normal, because the sentinel lives in the widget rather than in the data.

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
{synopt:{cmd:sd}}standard deviation (N-1){p_end}
{synopt:{cmd:var}}variance (N-1){p_end}
{synopt:{cmd:cv}}coefficient of variation, {cmd:sd}/{cmd:mean}{p_end}
{synopt:{cmd:iqr}}interquartile range, {cmd:p75} - {cmd:p25}{p_end}
{synopt:{cmd:skewness}}skewness{p_end}
{synopt:{cmd:p25}}25th percentile{p_end}
{synopt:{cmd:p50}}50th percentile (same as {cmd:median}){p_end}
{synopt:{cmd:p75}}75th percentile{p_end}
{synoptline}

{pstd}
Any percentile may be requested as {cmd:p}{it:#}, not only the three listed
above: {cmd:p10}, {cmd:p90} and {cmd:p97.5} are all accepted.  Percentiles
follow Stata's own rule rather than the interpolated one most software uses,
so {cmd:dash kpi p25(price)} reports the number {cmd:summarize, detail}
reports.  Variance and standard deviation divide by N-1, and skewness is
Stata's biased m3/m2^1.5 -- again, the values {cmd:summarize, detail} gives.

{pstd}
{ul:Options:}

{synoptset 24 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}}required; label displayed
    above the statistic value{p_end}
{synopt:{cmdab:nam:e}{cmd:(}{it:id}{cmd:)}}required; identifier for
    placement and filter exclusion{p_end}
{synopt:{cmdab:fmt:}{cmd:(}{it:format}{cmd:)}}a numeric Stata display
    format such as {cmd:%9.2f} or {cmd:%12.0fc}; anything else, including
    a string format such as {cmd:%12s}, is refused with an error{p_end}
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

{pstd}
A KPI is one card, in {cmd:dash build} and {cmd:dash serve} alike:
{cmd:update()} says how the card follows the dashboard, never which graph
it follows, and a {cmd:by()} graph does not split a card into one per
panel.  For a statistic of each group, register a card per group:
{cmd:dash kpi mean(mpg) if foreign == 0, title("Domestic") name(kdom)}.


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
{synopt:Shareable as a single file}    Yes                 No (.py, run with python){p_end}
{synopt:Filter widgets}                CustomJS (in-browser) Python callbacks{p_end}
{synopt:KPI recomputation on filter}   Yes (JS aggregation) Yes (Python/pandas){p_end}
{synopt:Histogram recompute on filter} Bar heights only    Yes, including bin edges{p_end}
{synopt:Kernel density on filter}      Yes (JS)            Yes (Python){p_end}
{synopt:Fit-line recompute on filter}  No                  Yes{p_end}
{synopt:Brush/lasso KPI update}        Yes                 Yes{p_end}
{synopt:Toolbar, save as PNG}          Yes                 Yes{p_end}
{synopt:{cmd:scheme()} / {cmd:theme()}}            Yes                 Yes{p_end}
{synopt:{cmd:layout()}, {cmd:tabs()}, {cmd:filterposition()}} Yes                 Yes{p_end}
{synopt:Bootstrap {cmd:layout(bs)}}         Yes, reflows        Yes, without reflow{p_end}
{synopt:Health endpoint}              n/a                 {cmd:/health}{p_end}
{synopt:Deployment}                    Email / open file   {cmd:python app.py}{p_end}
{synoptline}

{pstd}
{ul:What "histogram recompute" means.}  Standalone rescales the bars from
the rows that pass the filter but keeps the bin edges chosen when the
dashboard was built, so the bins do not move as you filter.  The server
recomputes the bins themselves from the filtered rows.  The same
distinction applies to any layer whose x-grid is derived from the data.

{pstd}
{ul:What "reflow" means.}  A saved {cmd:layout(bs)} grid rearranges itself as
the browser window narrows; the served one keeps the rows and spans it was
given at every width.  See {help dash##layout:Layout}.

{pstd}
{ul:Blocking behavior.}  {cmd:dash serve} blocks Stata until the server
is stopped.  Stop it by pressing Ctrl+C in the Stata console, or set
{cmd:timeout()} to limit the run time automatically.

{pstd}
{ul:Running the generated .py file independently.}
{cmd:dash build, saving(app.py) server} writes a self-contained server app
that embeds all data as base64.  Run it outside Stata with:

{phang2}{cmd:python app.py}{p_end}

{pstd}
It accepts {cmd:--port} {it:N}, {cmd:--address} {it:iface},
{cmd:--allow-websocket-origin} {it:host:port} (repeatable),
{cmd:--timeout} {it:minutes}, {cmd:--show}, {cmd:--trust-forwarded-for}, and
the rate limits {cmd:--sessions-per-client} {it:N},
{cmd:--new-clients-per-minute} {it:N} and {cmd:--sessions-per-minute}
{it:N} described below.  No browser window opens unless {cmd:--show} is
given, so the app is usable from a script or a batch job.

{pstd}
{cmd:bokeh serve app.py} also works and serves the same dashboard, with one
difference: {cmd:bokeh serve} owns its web application and gives an app
script no way to register an extra route, so {cmd:/health} exists only when
the app serves itself with {cmd:python app.py}.

{pstd}
{ul:Security.}  The app binds the loopback interface, so by default only
this machine can reach it.  {cmd:--address} {it:addr} opens it deliberately
-- {cmd:--address 0.0.0.0} listens on every interface -- and
{cmd:--allow-websocket-origin} {it:host:port} then admits the {cmd:Origin}
values a browser will send from there.

{pstd}
Understand what that second option is, before relying on it.  The
{cmd:Origin} allow-list filters a header the {it:client} supplies, so it
stops a page on another website from driving your dashboard in your browser.
It is not an access control: a client that is not a browser can omit the
header or forge an accepted one.  There is no password.

{pstd}
So the generated app is a single-user tool.  It embeds your whole dataset,
and anything that can reach the port can read it.  If you open it beyond
loopback, put it behind something that authenticates -- an SSH tunnel, a
reverse proxy, a firewall rule -- and treat the port as public otherwise.

{pstd}
Within the file, data values are base64-encoded so that no data content can
affect the Python source's syntax, and every user-supplied string reaches
the page as a Bokeh model property or an escaped HTML attribute rather than
as markup.

{pstd}
The page carries a Content-Security-Policy in both modes.  A saved dashboard
may run only the scripts and styles written into it and may load nothing
from anywhere; a served one may also load from, and connect to, the server
it came from, and nothing else.  {cmd:python app.py} also sends the policy as
a header on every response, {cmd:/health} included, adding
{cmd:frame-ancestors 'none'} so that no other site can frame the dashboard,
and sends {cmd:X-Content-Type-Options: nosniff},
{cmd:X-Frame-Options: DENY} and {cmd:Referrer-Policy: no-referrer} with it.
{cmd:bokeh serve app.py} sends none of these headers, so its page carries
the policy but can be framed.

{pstd}
Session creation and {cmd:/health} are rate limited, each separately, so a
health probe never spends the dashboard's budget.  The client is identified
by the peer address, not by {cmd:X-Forwarded-For}, because that header is set
by the client unless a proxy you control overwrites it -- trusting it made the
limit bypassable with a single header.  Behind such a proxy, pass
{cmd:--trust-forwarded-for} so that each end user gets their own bucket
rather than sharing the proxy's.

{pstd}
Three limits apply to new sessions, each over the last minute:

{phang2}{cmd:--sessions-per-client} {it:N} (default 60) -- sessions one
    client may open.{p_end}
{phang2}{cmd:--new-clients-per-minute} {it:N} (default 60) -- clients the
    server is not already tracking, admitted between them.  A client that
    presents a new address on every request -- possible through a proxy that
    passes the header through unchanged -- is held to one client's rate
    rather than escaping the limit.{p_end}
{phang2}{cmd:--sessions-per-minute} {it:N} (default 600) -- all sessions
    together.{p_end}

{pstd}
Each takes a whole number from 1 to 1,000,000.  A client over a limit gets a
{cmd:429 Too Many Requests} page, and the server logs the refusal -- once a
minute per limit, so a flood cannot flood the log -- naming the limit and its
flag.  No client that is still active is ever forgotten to make room for new
ones, so a flood of addresses cannot reset a real client's count.

{pstd}
{ul:Recomputation.}  A slider recomputes the dashboard when you release it,
not at every step of the drag.  In each browser session, each filter widget
and each brushed graph then recomputes at most 10 times in a burst and twice
a second after that; changes that arrive faster are folded into one
recomputation with the latest values.  A script that moves a widget in a
loop therefore cannot monopolise the server, which runs one recomputation at
a time for every session.

{pstd}
The generated app embeds your whole dataset, base64-encoded.  Treat the
{cmd:.py} file as you would the data: {cmd:dash serve} writes its copy to a
Stata temporary file that Stata erases when the command ends, and a file you
name with {cmd:saving()} is yours to manage.


{marker limits}
{title:Resource limits}

{pstd}
Every input that decides how much {cmd:dash} builds has a limit, so that no
dataset, option or registry can produce an unbounded file or exhaust memory.
Each limit has a default, a ceiling that nothing moves, and a global macro
that moves it for the rest of the session:

{synoptset 28 tabbed}{...}
{synopthdr:global}
{synoptline}
{synopt:{cmd:$dash_max_cells}}values embedded, observations times the
    variables a dashboard uses; default 5,000,000, at most 20,000,000.  Over
    it the dashboard is refused with {cmd:r(134)} before anything is
    exported.{p_end}
{synopt:{cmd:$dash_max_graphs}}graphs and KPI cards in the registry; default
    100, at most 1,000.  A new name past it is refused with
    {cmd:r(134)}.  It also bounds the cells of a {cmd:layout()} grid, which
    is refused with {cmd:r(198)} when larger.{p_end}
{synopt:{cmd:$dash_max_plots}}plots in one graph, where each y variable of
    {cmd:scatter y1 y2 x} is one; default 100, at most 1,000.  Refused with
    {cmd:r(134)}.{p_end}
{synopt:{cmd:$dash_max_filter_options}}values one {cmd:type(dropdown)}
    filter lists; default 1,000, at most 100,000.  Over it a numeric or date
    variable is drawn as {cmd:type(range)} and a string variable lists its
    first values in sort order.{p_end}
{synopt:{cmd:$dash_max_by_groups}}panels one {cmd:by()} graph draws; default
    100, at most 1,000.  The first groups in sort order are drawn.{p_end}
{synopt:{cmd:$dash_max_tabs}}tabs; default 50, at most 500.  The first are
    drawn.{p_end}
{synopt:{cmd:$dash_max_filters}}filter widgets; default 20, at most 200.
    The first are built.{p_end}
{synoptline}

{pstd}
A limit that clamps says so in a note naming the limit and the global that
raises it; a limit that refuses says so in its error.  For example,

{phang2}{cmd:. global dash_max_by_groups 250}{p_end}

{pstd}
lets one {cmd:by()} graph draw 250 panels.  A global must be a whole number
from 1 to its ceiling, written in digits; anything else is refused with
{cmd:r(198)}.  An unset global means the default.  {cmd:dash clear} does not
drop these globals, because they are settings rather than registry;
{cmd:macro drop dash_max_*} does.

{pstd}
{ul:Why the data limit counts every observation.}  {cmd:dash} exports every
observation of the variables a dashboard uses and applies {cmd:if} and
{cmd:in} itself, because different plots can carry different qualifiers.  A
qualifier therefore does not reduce what is exported or held in memory, so
reduce the data first -- {cmd:keep}, {cmd:drop}, {cmd:sample} or
{cmd:collapse}, inside {cmd:preserve} and {cmd:restore}.  Above 1,000,000
values {cmd:dash} notes the size the file will be, at about 24 bytes a value;
measured, 4,000,000 values made a 95 MB page and took 2.1 GB of memory to
render.

{pstd}
{ul:A served dashboard} has rate limits of its own; see
{help dash##server_mode:Server Mode}.


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
{phang2}{cmd:. * Run outside Stata:  python app.py --show}{p_end}


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
The panels are arranged the same way wherever the graph is drawn -- in the
dashboard's grid, in a tab, or in a {cmd:layout(bs)} cell -- and in both
{cmd:dash build} and {cmd:dash serve}: in {it:#} columns with
{cmd:cols(}{it:#}{cmd:)}, and otherwise in as many columns as the square
root of the number of panels, rounded up.  A {cmd:cols()} of more columns
than there are panels puts them all in one row.
Value labels are used for facet panel titles when available.
Multiple by-variables produce composite labels (e.g. "Domestic / 3").
One graph draws at most 100 panels: over that, the first 100 groups in
sort order are drawn and a note names the limit (see
{help dash##limits:Resource limits}).
{cmd:cols()}, {cmd:total} and {cmd:missing} are the {cmd:by()} sub-options
{cmd:dash} implements.  Any other sub-option of Stata's {cmd:by()} -- for
example {cmd:rows()}, {cmd:holes()} or {cmd:compact} -- is accepted, named
in a warning, and ignored.
{cmd:by()} combines with {cmd:link()}: a faceted graph inside a link group
draws its panels as views over the one shared data source, so a box-select
in any panel highlights the matching observations in every other panel and
in every other linked graph.

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
{synopt:{cmdab:ml:abel(}{it:varname}{cmd:)}}annotate each observation with
    the value of {it:varname}; applies to scatter, line, connected, bar,
    spike, dot, dropline, and all range plot types (rspike, rcap, rline,
    rarea, rbar, rcapsym){p_end}
{synopt:{cmdab:mlabc:olor(}{it:color}{cmd:)}}color of the label text{p_end}
{synopt:{cmdab:mlabs:ize(}{it:size}{cmd:)}}size keyword or number; e.g.
    {cmd:small}, {cmd:medium}, {cmd:large}{p_end}
{synopt:{cmdab:mlabp:osition(}{it:#}{cmd:)}}clock position for label
    placement relative to the data point, an integer from 0 to 12;
    3 = right (default), 12 = above, 6 = below, 9 = left.  A value
    outside 0 to 12, or a name {cmd:dash} does not recognise, is
    reported and 3 used, as {cmd:twoway} notes it{p_end}
{synopt:{cmdab:mlabg:ap(}{it:#}{cmd:)}}additional offset in pixels added to
    the clock-position offset{p_end}
{synoptline}

{pstd}
For range plot types, labels are placed at the upper boundary (y2 variable).

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, mlabel(make) mlabcolor(navy) mlabsize(small)}{p_end}


{marker smoother_options}
{title:Statistical Layer Options}

{pstd}
The following plot-level options belong to the statistical layers; each
entry names the plot types that take it, as {helpb twoway} does.  An
option that changes an estimate is honoured or refused, never accepted
and ignored.  {cmd:fpfit} and {cmd:fpfitci} take none of the smoothing
options — see below.

{synoptset 20}{...}
{synopt:{opt bwidth(#)}}half-width of the smoothing kernel, as an
    {bf:absolute bandwidth in the units of x}, exactly as in
    {helpb twoway lpoly}.  With no {cmd:bwidth()} a rule-of-thumb bandwidth
    is computed from the data.  {cmd:bw()} abbreviates it here, on
    {cmd:lpolyci}, {cmd:lowess} and {cmd:kdensity}, as in {cmd:twoway};
    on {cmd:bar}, {cmd:rbar}, {cmd:histogram}, {cmd:dot} and {cmd:spike}
    {cmd:dash} reads {cmd:bw()} as {cmd:barwidth()}, and on any other
    plot type names it in the note{p_end}
{synopt:{opt degree(#)}}polynomial degree, an integer from 0 to 3; 0 =
    Nadaraya–Watson kernel estimator (default), 1 = local linear,
    2 = local quadratic, 3 = local cubic.  Anything else is refused:
    {cmd:dash} fits local polynomials up to degree 3{p_end}
{synopt:{opt kernel(name)}}{cmd:epanechnikov} (default), {cmd:epan2},
    {cmd:biweight}, {cmd:cosine}, {cmd:gaussian}, {cmd:parzen},
    {cmd:rectangle} or {cmd:triangle}; any other word is refused{p_end}
{synopt:{opt n(#)}}number of points at which {cmd:lpoly}, {cmd:lpolyci}
    and {cmd:kdensity} evaluate, an integer from 2 to 10000, since
    {cmd:dash} evaluates up to 10000 points.  {cmd:lpoly} and
    {cmd:lpolyci} follow {cmd:twoway}: 50 points over the observed range
    by default, never more than the dataset has observations, and every
    observation's worth when the dataset has fewer than 50 -- counting
    the whole dataset, not the plot's sample, so an {cmd:if} or a
    {cmd:by()} panel keeps the 50-point grid.  {cmd:kdensity} defaults to
    300 points from the minimum to the maximum of the data, as in
    {cmd:twoway}.  On {cmd:mspline} it is the number of points drawn
    between each pair of adjacent knots, default 10, from 1 to 300 as in
    {cmd:twoway}{p_end}
{synopt:{opt bands(#)}}number of equal-width bands for {cmd:mspline} and
    {cmd:mband}, an integer from 1 to 200, as in {cmd:twoway}.  The
    default is Stata's: round(min(10 log10 {it:N}, sqrt {it:N})), and at
    least min({it:N}, 2){p_end}
{synopt:{opt discrete}}{cmd:histogram} only: one bar per distinct value;
    see below.  Refused together with {cmd:bin()}, r(198){p_end}
{synopt:{opt stdp}}{cmd:lfitci} and {cmd:qfitci} only: the band is built
    on the standard error of the prediction (the default){p_end}
{synopt:{opt stdf}}{cmd:lfitci} and {cmd:qfitci} only: on the standard
    error of the forecast, sqrt(stdp^2 + rmse^2){p_end}
{synopt:{opt stdr}}{cmd:lfitci} and {cmd:qfitci} only: on the standard
    error of the residual, sqrt(rmse^2 - stdp^2), left missing where
    that is negative.  Two of {cmd:stdp}, {cmd:stdf} and {cmd:stdr}
    together are refused, r(198), as {cmd:twoway} refuses them{p_end}
{synopt:{opt mean}}{cmd:lowess} only: a running mean rather than a
    running line{p_end}
{synopt:{opt noweight}}{cmd:lowess} only: the tricube weights are
    dropped{p_end}
{synopt:{opt adjust}}{cmd:lowess} only: the smooth is rescaled so that
    its mean equals the mean of {it:yvar} -- over every observation in
    the data, as {cmd:lowess} computes it, whatever the {cmd:if} or the
    {cmd:by()} panel{p_end}
{synopt:{opt logit}}{cmd:lowess} only: the logit of the smooth is
    drawn, for a 0/1 {it:yvar}; applied after {cmd:adjust}{p_end}
{synoptline}

{pstd}
{cmd:lpoly} and {cmd:lpolyci} implement kernel-weighted local polynomial
regression — the same smoother underlying Stata's {helpb twoway lpoly},
with the same default kernel ({cmd:epanechnikov}) and the same
{cmd:degree(0)} default.  At a given {cmd:bwidth()} the curve is Stata's
at every degree -- including where a window holds fewer distinct x
values than the degree needs, where the degree drops as Stata's does.
A grid point at which fewer than two observations have positive kernel
weight is left missing, as Stata leaves it, and the line joins the
points on either side of it, as {cmd:twoway lpoly} draws it; a
{cmd:bwidth()} too narrow for any window to hold two observations draws
nothing.  The grid is {cmd:n()} points over the observed range, sized as
{cmd:twoway} sizes it (see {cmd:n()} above).

{pstd}
{bf:Note on {cmd:bwidth()} for {cmd:lowess}.}  Stata gives the same option
name two different meanings: for {helpb twoway lpoly} it is an absolute
bandwidth in x units, while for {helpb twoway lowess} it is the
{it:fraction} of the sample used in each local regression (default 0.8).
{cmd:dash} follows Stata in both cases.

{pstd}
{bf:Default bandwidth.}  With no {cmd:bwidth()}, {cmd:dash} uses a
Fan–Gijbels rule of thumb.  Stata computes its own rule of thumb in
compiled Mata and it is not reproducible from the published documentation,
so the two agree only approximately: measured against {cmd:r(bwidth)} on
Stata's example datasets, {cmd:dash}'s default is 9.7% below Stata's on
{cmd:auto} mpg on weight, 22% below on {cmd:auto} price on mpg and on
rep78, 17% below on mpg on weight with {cmd:[aweight=price]}, and 5.7%,
6.8% and 14.2% above on {cmd:sp500}, {cmd:nlsw88} and {cmd:census};
below eight observations it is a tenth of the range (34% above Stata's
at seven).  Specify {cmd:bwidth()} to reproduce a Stata smoother
exactly.

{pstd}
{cmd:lowess} is Stata's smoother, not a library's: the sample is sorted
by x with ties kept in dataset order, each observation is fitted by a
weighted running line over the {cmd:bwidth()} fraction of the sample
centred on it by position, with tricube weights on the distance, and no
robustness iterations are run — the rule in {manhelp lowess R:lowess},
Methods and formulas.  A window whose x values are all equal has no
line, and the running line is missing there, as Stata's is; the line
joins the points on either side.  Fewer than three observations, or an
x that does not vary, draw nothing.  {cmd:mean} fits a running mean
instead, {cmd:noweight} drops the tricube weights, {cmd:adjust}
multiplies the smooth by the mean of {it:yvar} over every observation in
the data divided by the mean of the smooth (a smooth whose mean is zero
has no adjusted value), and {cmd:logit} draws ln({it:s}/(1 - {it:s}))
after clamping {it:s} to [1/{it:N}, 1 - 1/{it:N}] -- a missing smooth,
as in Stata, becoming 1 - 1/{it:N} -- {cmd:adjust} first when both are
given.  {cmd:lowess} takes no weights, in {cmd:twoway} or here.
{cmd:dash} no longer needs statsmodels for it.

{pstd}
{cmd:mspline} is Stata's estimator: the x range is cut into
{cmd:bands()} equal-width bands, the cross-median (the median x and the
median y) of each non-empty band is a knot, and a cubic spline through
the knots is drawn at the knots plus {cmd:n()} equally spaced points
between each adjacent pair — a natural cubic spline, which reproduces
Stata's plotted points to the precision Stata stores them at; with one
or two knots only the knots are drawn, as in Stata.  An observation on
a band's edge belongs to the band above it.  {cmd:mband} draws the same
cross medians as a line, from two observations up.  A weight on either
is accepted and, as in {cmd:twoway}, changes nothing -- not even a
missing or zero weight drops its observation.

{pstd}
{cmd:fpfit} and {cmd:fpfitci} implement degree-2 fractional polynomial
fitting (Royston & Altman, 1994), selecting the pair of powers from
{c -(}{cmd:–2}, {cmd:–1}, {cmd:–0.5}, {cmd:0}, {cmd:0.5}, {cmd:1},
{cmd:2}, {cmd:3}{c )-} that minimises the residual sum of squares over
all 36 pairs, a repeated pair ({it:p}, {it:p}) meaning x^{it:p} and
x^{it:p} ln x, as in {helpb fracpoly}.  x need not be positive: when
its minimum is zero or less the origin is shifted as {cmd:fracpoly}
shifts it, by the smallest positive spacing of the sorted x values
minus the minimum, and x is then scaled by the power of ten
{cmd:fracpoly} takes from its range before the powers are chosen; every
observation is used.  Like Stata, both evaluate at the distinct observed
x values rather than on a fixed grid, from two observations up.
{cmd:fpfitci}'s band is {it:t} times the standard error of the
prediction with {it:N} - 3 degrees of freedom ({it:N} minus the number
of terms the design supports, when x takes only two values); with none
to spare the fit is drawn with no band, and a {it:y} that does not vary
draws nothing, as in Stata.  It takes {cmd:stdp} only.  On a date-time
x, whose offset is large against its range, Stata's choice between two
nearly equal models can differ from {cmd:dash}'s; the curves then differ
by no more than 5e-4 of their range (measured).

{pstd}
{bf:{cmd:fpfit} does not take {cmd:bwidth()} or {cmd:degree()}.}  Earlier
versions of this help wrongly listed them.  Stata rejects both with r(198)
— a fractional polynomial has no bandwidth at all, and its degree is
spelled {cmd:estopts(degree(#))}.  {cmd:dash} accepts them so a pasted
command still runs, and reports that they were ignored.

{pstd}
{cmd:histogram} with {cmd:discrete} draws one bar per distinct value, of
width {cmd:width()} or, by default, the smallest positive spacing
between the distinct values (1 when there is only one), each bar centred
on its value; {cmd:start()} does not move the bars, as in Stata, and a
value past the last bar's edge (a {cmd:width()} coarser than the data's
spacing) is counted in the last bar, as Stata counts it.
{cmd:discrete} with {cmd:bin()} is refused, r(198), as {cmd:twoway}
refuses it.  On any {cmd:histogram} a {cmd:start()} above the smallest
value of the plot's sample is refused, r(198), as {cmd:twoway} refuses
it ({cmd:option start() may not be larger than minimum of} ...); a
variable whose values are all equal is one bar of width 1, as in Stata.
{cmd:kdensity} evaluates on {cmd:n()} points from the minimum to the
maximum of the data, as {cmd:twoway kdensity} does.

{pstd}
{cmd:fpfitci}, {cmd:lpolyci}, {cmd:lfitci} and {cmd:qfitci} draw a
confidence band at {cmd:level()}, defaulting to the session's
{cmd:c(level)} — so {cmd:set level 90} is honoured.
{cmd:level(}{it:#}{cmd:)} must be a number strictly between 0 and 100 and
is refused otherwise, with r(198).  {cmd:lfitci} and {cmd:qfitci} build
the band on {cmd:stdp}, {cmd:stdf} or {cmd:stdr}, {it:t} times that
standard error with the same {it:t} for all three; with an
{cmd:aweight}, {cmd:stdf} and {cmd:stdr} are refused as {cmd:twoway}
refuses them ({cmd:not possible with weighted data}, r(135)), and with a
{cmd:pweight} likewise (r(198)).  An {it:x} with two values fits the
line ({cmd:qfit} and {cmd:qfitci} omit x^2, as {cmd:regress} does), and
three observations draw the quadratic fit with no band.
{cmd:lpolyci}'s band is a bootstrap percentile band, not Stata's, every
resample evaluated on the drawn line's own grid.  The bound of every checked
option is listed under {help dash##validation:Option values}.

{pstd}
{it:Example:}
{phang2}{cmd:. dash (scatter mpg weight) (lpoly mpg weight, bwidth(0.4)), saving(lp.html)}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (fpfit mpg weight), saving(fp.html)}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (lfitci mpg weight, stdf), saving(lf.html)}{p_end}
{phang2}{cmd:. dash histogram rep78, discrete saving(h.html)}{p_end}


{marker weights}
{title:Weights}

{pstd}
A weight is written inside a plot as {cmd:twoway} writes it —
{cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=}{it:varname}{cmd:]}
or {cmd:[pweight=}{it:varname}{cmd:]} — and each statistical layer takes
the types {cmd:twoway} lets it take:

{synoptset 32}{...}
{synopt:{cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}}{cmd:aweight}, {cmd:fweight}, {cmd:pweight}{p_end}
{synopt:{cmd:fpfit}, {cmd:fpfitci}}{cmd:aweight}, {cmd:fweight}, {cmd:pweight}{p_end}
{synopt:{cmd:lpoly}, {cmd:lpolyci}, {cmd:kdensity}}{cmd:aweight}, {cmd:fweight}{p_end}
{synopt:{cmd:histogram}}{cmd:fweight}{p_end}
{synopt:{cmd:mspline}, {cmd:mband}}{cmd:aweight}, {cmd:fweight}, {cmd:pweight} — accepted and inert, as in {cmd:twoway}{p_end}
{synopt:{cmd:lowess}}none{p_end}
{synoptline}

{pstd}
The meaning is Stata's: an {cmd:aweight} is normalised to sum to
{it:N}; an {cmd:fweight} replicates observations, so {it:N} is the sum of
the weights; a {cmd:pweight} gives the {cmd:aweight} estimates with a
robust standard error for the band.  A weight's values are treated as
{cmd:twoway} treats them, checked over the plot's own sample: a
non-integer {cmd:fweight} is r(401) on {cmd:lfit}, {cmd:lfitci},
{cmd:lpoly}, {cmd:lpolyci}, {cmd:histogram} and {cmd:kdensity}, a
negative {cmd:fweight} r(402) on the last four, and a negative
{cmd:aweight} r(402) on {cmd:kdensity}, {cmd:lpoly} and {cmd:lpolyci}.
Elsewhere the command is accepted and the layer drawn as {cmd:twoway}
draws it: {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and {cmd:qfitci} leave a
negative weight's observation out; {cmd:qfit}, {cmd:qfitci}, {cmd:fpfit}
and {cmd:fpfitci} draw nothing for a non-integer {cmd:fweight}, and
{cmd:fpfit} and {cmd:fpfitci} nothing for any negative weight, each with
a note.  A zero weight leaves its observation out everywhere.  A weight {cmd:twoway} refuses,
{cmd:dash} refuses with the same code and words: {cmd:[iweight=]} on any
plot type, any weight on {cmd:lowess} ({cmd:weights not allowed}),
{cmd:[aweight=]} or {cmd:[pweight=]} on {cmd:histogram}, and
{cmd:[pweight=]} on {cmd:kdensity}, {cmd:lpoly} or {cmd:lpolyci} — each
r(101).  The weight must be one existing variable, abbreviated as
{cmd:twoway} abbreviates a variable.  {cmd:twoway} also accepts an
expression there; {cmd:dash} cannot evaluate one before the data leave
Stata, so it is refused with r(198) and the remedy:

{phang3}{cmd:. dash lfit mpg weight [aw=price+1]}{p_end}
{phang3}{cmd:dash: [aweight=price+1] must name one variable; dash cannot evaluate a weight expression. Generate it first: generate double w = price+1}{p_end}

{pstd}
On {cmd:scatter} and the other glyph layers a weight is accepted so a
pasted command still runs, but it is not drawn ({cmd:twoway scatter}
sizes its markers by an {cmd:aweight}; {cmd:dash} does not), and it is
named in the note by type, never by variable, as {cmd:[aweight]}.  The
weight variable is exported with the data.

{pstd}
{it:Example:}
{phang2}{cmd:. dash (scatter mpg weight) (lfitci mpg weight [aw=price]), saving(w.html)}{p_end}


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
{synopt:{cmdab:bgc:olor(}{it:color}{cmd:)}}shorthand for
    {cmd:graphregion(color())}{p_end}
{synopt:{opt plotbgcolor(color)}}shorthand for
    {cmd:plotregion(color())}.  Abbreviation: {cmd:pbgc()}{p_end}
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
{synopt:{cmdab:xt:itle(}{it:string}{cmd:)}}label for the x axis{p_end}
{synopt:{cmdab:yt:itle(}{it:string}{cmd:)}}label for the y axis{p_end}
{synopt:{cmdab:xl:abel(}{it:#}[{it:#} ...]{cmd:)}}custom x-axis tick positions{p_end}
{synopt:{cmdab:yl:abel(}{it:#}[{it:#} ...]{cmd:)}}custom y-axis tick positions{p_end}
{synopt:{cmdab:xl:abel(}{it:#}[{it:#} ...]{cmd:, format(}{it:fmt}{cmd:))}}custom ticks with format string{p_end}
{synopt:{cmdab:xsc:ale(log)}}display the x axis on a log scale{p_end}
{synopt:{cmdab:ysc:ale(log)}}display the y axis on a log scale{p_end}
{synopt:{cmdab:xli:ne(}{it:#}[{it:#} ...]{cmd:)}}draw vertical reference lines at x = {it:#}{p_end}
{synopt:{cmdab:yli:ne(}{it:#}[{it:#} ...]{cmd:)}}draw horizontal reference lines at y = {it:#}{p_end}
{synopt:{cmd:note(}{it:string}{cmd:)}}footnote text below the figure{p_end}
{synopt:{cmdab:cap:tion(}{it:string}{cmd:)}}caption text below the figure{p_end}
{synopt:{cmdab:asp:ectratio(}{it:#}{cmd:)}}HEIGHT divided by WIDTH, as in
    Stata (e.g. {cmd:aspectratio(1)} for a square plot, {cmd:aspectratio(0.5)}
    for one half as tall as it is wide){p_end}
{synopt:{cmdab:leg:end(off)}}hide the legend{p_end}
{synopt:{cmdab:leg:end(on)}}draw a legend on a graph that has fewer than two
    keys, which would otherwise have none{p_end}
{synopt:{cmdab:leg:end(}{it:position}{cmd:)}}place legend: {cmd:top}, {cmd:bottom}, {cmd:left}, {cmd:right}{p_end}
{synopt:{cmdab:leg:end(position(}{it:#}{cmd:))}}place legend by Stata clock
    position: 12 is above, 3 right, 6 below, 9 left{p_end}
{synopt:{cmdab:leg:end(ring(0))}}keep the legend inside the plot region
    rather than beside it{p_end}
{synopt:{cmdab:leg:end(cols(}{it:#}{cmd:))}}arrange legend entries in {it:#} columns{p_end}
{synopt:{cmdab:leg:end(rows(}{it:#}{cmd:))}}arrange legend entries in {it:#} rows{p_end}
{synopt:{cmdab:leg:end(order(}{it:numlist}{cmd:))}}reorder the entries; an
    entry left out of {it:numlist} is dropped from the legend{p_end}
{synopt:{cmdab:leg:end(size(}{it:size}{cmd:))}}font size of the legend text{p_end}
{synopt:{cmdab:leg:end(label(}{it:#} {it:"text"}{cmd:))}}override the label for entry {it:#}{p_end}
{synopt:{cmdab:xsiz:e(}{it:#}{cmd:)}}graph width in inches{p_end}
{synopt:{cmdab:ysiz:e(}{it:#}{cmd:)}}graph height in inches{p_end}
{synopt:{cmdab:xtic:k(}{it:#}[{it:#} ...]{cmd:)}}x-axis tick positions
    without labels{p_end}
{synopt:{cmdab:ytic:k(}{it:#}[{it:#} ...]{cmd:)}}y-axis tick positions
    without labels{p_end}
{synoptline}

{pstd}
{ul:Axis labels.}  {cmd:xlabel()} and {cmd:ylabel()} take Stata's own
vocabulary, not just a list of numbers:

{synoptset 24}{...}
{synopt:{it:numlist}}explicit tick positions, e.g. {cmd:xlabel(1000 2000 3000)}{p_end}
{synopt:{cmd:#}{it:N}}about {it:N} ticks, chosen over the data range{p_end}
{synopt:{it:a}{cmd:(}{it:b}{cmd:)}{it:c}}from {it:a} to {it:c} in steps of {it:b}{p_end}
{synopt:{cmd:minmax}}label only the smallest and largest values{p_end}
{synopt:{cmd:none}}draw no tick labels{p_end}
{synoptline}

{pstd}
Any of those may be followed by a comma and the sub-options
{cmd:format(}{it:fmt}{cmd:)}, {cmd:labsize(}{it:size}{cmd:)},
{cmd:angle(}{it:#}{cmd:)}, and {cmd:grid} or {cmd:nogrid}.  The axis range
itself is set with {cmd:xscale(range(}{it:a b}{cmd:))} /
{cmd:yscale(range(}{it:a b}{cmd:))}.

{pstd}
{it:Examples:}
{phang2}{cmd:. dash scatter mpg weight, xlabel(#8, grid) ylabel(10(5)40, format(%9.0f))}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(minmax) yscale(range(0 50))}{p_end}

{pstd}
{ul:Secondary axes.}  Write {opt yaxis(2)} on any plot layer to put it on a
right-hand y axis scaled to that layer's own data, or {opt xaxis(2)} for a
top x axis.  The secondary range is computed from the data on that axis.
Both are plot-level options, given inside the layer's parentheses.  Either
takes 1 or 2 only: {cmd:dash} draws two axes where {cmd:twoway} allows
nine, and any other value is refused.

{synoptset 38}{...}
{synopt:{opt ytitle2(string)}}title for the right-hand y axis.
    Abbreviation: {cmd:yti2()}{p_end}
{synopt:{opt ylabel2(numlist)}}tick positions for the right-hand y axis.
    Abbreviation: {cmd:yla2()}{p_end}
{synopt:{opt yscale2(log)}}log scale on the right-hand y axis.
    Abbreviation: {cmd:ysc2()}{p_end}
{synopt:{opt xtitle2(string)}}title for the top x axis.
    Abbreviation: {cmd:xti2()}{p_end}
{synopt:{opt xlabel2(numlist)}}tick positions for the top x axis.
    Abbreviation: {cmd:xla2()}{p_end}
{synopt:{opt xscale2(log)}}log scale on the top x axis.
    Abbreviation: {cmd:xsc2()}{p_end}
{synoptline}

{pstd}
{it:Example:}
{phang2}{cmd:. dash (line sales year) (line margin year, yaxis(2)), ytitle2(Margin %)}{p_end}


{marker colorvar}
{title:Mapping a Variable to Colour}

{pstd}
A plot layer may take its colour from a third variable rather than from the
scheme's series cycle.  {cmd:colorvar()} is Stata 18's own option and behaves
as it does there; the four that configure it are specific to {cmd:dash}.

{synoptset 38}{...}
{synopt:{opt colorvar(varname)}}colour each observation by {it:varname}.
    Abbreviations: {cmd:colv()}, {cmd:cv()}{p_end}
{synopt:{opt colordiscrete}}treat {it:varname} as categorical rather than
    continuous{p_end}
{synopt:{opt colorcuts(numlist)}}explicit break points for the colour
    bins{p_end}
{synopt:{cmdab:colpal:ette(}{it:name}{cmd:)}}the palette to map through:
    {cmd:viridis} (the default), {cmd:magma}, {cmd:inferno}, {cmd:plasma},
    {cmd:cividis}, {cmd:turbo}, {cmd:greys}, {cmd:blues} or {cmd:reds}{p_end}
{synopt:{cmdab:colorn:levels(}{it:#}{cmd:)}}number of colour levels for a
    continuous {it:varname}; an integer from 2 to 256{p_end}
{synopt:{cmdab:colorm:issing(}{it:color}{cmd:)}}colour drawn for observations
    where {it:varname} is missing{p_end}
{synoptline}

{pstd}
A continuous {cmd:colorvar()} draws a colour bar beside the figure; a
discrete one draws a legend entry per level.

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, colorvar(price) colpalette(magma) colornlevels(8)}{p_end}

{pstd}
{ul:When a legend appears.}  As in {helpb twoway}, a legend is drawn only
when the graph has two or more keys: a lone {cmd:scatter} gets none, a
{cmd:scatter} with an {cmd:lfit} over it gets one.  {cmd:legend(on)} forces
one onto a single-key graph and {cmd:legend(off)} removes it from any graph.


{marker geometry}
{title:Figure proportions}

{pstd}
A {cmd:dash} dashboard is responsive: figures stretch to the width they are
given rather than being drawn at a fixed pixel size.  {cmd:xsize()},
{cmd:ysize()} and {cmd:aspectratio()} therefore set a figure's PROPORTIONS,
and the figure fills the width available at that shape.

{pstd}
The precedence, highest first:

{phang2}1. {cmd:xsize()} and {cmd:ysize()}, in inches, as in Stata.  Either
    alone keeps the other from the scheme: under {cmd:stcolor},
    {cmd:xsize(9)} gives 4.5 x 9, exactly as {helpb twoway} does.{p_end}
{phang2}2. {cmd:aspectratio(}{it:#}{cmd:)}, which in Stata is
    {bf:height divided by width} -- {cmd:aspectratio(0.5)} is half as tall as
    it is wide.{p_end}
{phang2}3. The active scheme's {cmd:graphsize x} and {cmd:graphsize y}, so a
    {cmd:dash} dashboard has the proportions of your other graphs without
    your asking.{p_end}

{pstd}
The ratio is honoured within a height band.  Outside it the ratio yields, so
that a single square panel cannot fill an entire screen and a very wide panel
does not collapse to an unreadable sliver on a phone.

{pstd}
{it:Examples:}
{phang2}{cmd:. dash scatter mpg weight, xsize(10) ysize(2)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, aspectratio(1)}{p_end}

{pstd}
{it:Examples:}
{phang2}{cmd:. dash scatter mpg weight, xtitle(Weight (lbs)) ytitle(Mileage)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xscale(log) yscale(log)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xline(3000) yline(20 30)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(1000 2000 3000 4000) ylabel(10 20 30 40)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, note(Source: 1978 Automobile Data)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, aspectratio(0.75)}{p_end}


{marker markers}
{title:Marker and Transparency Options}

{pstd}
These plot-level options are supported and honoured.  They were documented
under {it:Unsupported Stata twoway options} in earlier versions of this help,
which was wrong in both directions: they work, and the note {cmd:dash} prints
has never named them.

{synoptset 28}{...}
{synopt:{opt jitter(#)}}add uniform noise scaled to {it:#}% of the axis range
    to both coordinates; {it:#} must be a number from 0 to 100.  Supported
    on {cmd:scatter}, {cmd:dot}, {cmd:dropline} and {cmd:scatteri}{p_end}
{synopt:{opt jitterseed(#)}}random-number seed for {cmd:jitter()}, spelled as
    in Stata; {it:#} must be a non-negative integer.  With no seed the noise
    differs on every render{p_end}
{synopt:{opt jseed(#)}}a {cmd:dash} synonym for {cmd:jitterseed()}, with the
    same bound; if both are given, {cmd:jseed()} wins{p_end}
{synopt:{cmdab:msa:ngle(}{it:#}{cmd:)}}rotate every marker in the layer
    {it:#} degrees clockwise; {it:#} must lie between -360 and 360, as in
    {cmd:twoway}.  Valid for {cmd:scatter}, {cmd:dot},
    {cmd:dropline}, {cmd:connected} and {cmd:scatteri}{p_end}
{synopt:{cmdab:mal:pha(}{it:#}{cmd:)}}opacity of the markers, 0-100{p_end}
{synopt:{cmdab:lal:pha(}{it:#}{cmd:)}}opacity of the lines, 0-100{p_end}
{synopt:{cmdab:fa:lpha(}{it:#}{cmd:)}}opacity of the fill, 0-100{p_end}
{synoptline}

{pstd}
Stata's {cmd:color%alpha} notation works too, so {cmd:mcolor(red%50)} and
{cmd:mcolor(red) malpha(50)} are the same thing.

{pstd}
{it:Example:}
{phang2}{cmd:. dash scatter mpg weight, jitter(5) jitterseed(12345) malpha(60)}{p_end}


{marker scheme}
{title:Stata scheme support}

{pstd}
{cmd:scheme()} applies a named Stata graph scheme to the whole dashboard.
With no {cmd:scheme()} and no {cmd:theme()}, {cmd:dash} follows the session's
own {cmd:c(scheme)}, so a dashboard has the look of every other graph you
draw without your asking.

{pstd}
{cmd:dash} ships faithful translations of twenty StataCorp schemes:

{synoptset 16}{...}
{synopt:{cmd:stcolor}}Stata 18+ default{p_end}
{synopt:{cmd:stcolor_alt}}{p_end}
{synopt:{cmd:stgcolor}}{p_end}
{synopt:{cmd:stgcolor_alt}}{cmd:stcolor_alt} at the manuals' page size{p_end}
{synopt:{cmd:stmono1}}{p_end}
{synopt:{cmd:stmono2}}{p_end}
{synopt:{cmd:stsj}}{p_end}
{synopt:{cmd:sttrans}}{cmd:s2color} restyled to {cmd:stcolor}'s look
    (white background, legend at the right) with a colourblind-friendly
    palette (Paul Tol's muted colours) declared at twenty percent
    opacity ({cmd:%20}), which {cmd:dash} carries into the glyphs in both
    modes, as Stata draws it{p_end}
{synopt:{cmd:s2color}}the default from Stata 10 to 17{p_end}
{synopt:{cmd:s2color8}}{cmd:s2color} with Stata's {cmd:8} colour variants
    ({cmd:navy8}, {cmd:ltbluishgray8}, {cmd:bluishgray8}) for the
    background, grid, boxes and the first and last series{p_end}
{synopt:{cmd:s2mono}}{p_end}
{synopt:{cmd:s2manual}}{cmd:s2mono} at the manuals' page size, as printed in
    every manual but [G]{p_end}
{synopt:{cmd:s2gmanual}}{cmd:s2mono} at the manuals' page size with each
    line plot in its own solid grey, as printed in [G]{p_end}
{synopt:{cmd:s2gcolor}}{p_end}
{synopt:{cmd:s1color}}{p_end}
{synopt:{cmd:s1mono}}{p_end}
{synopt:{cmd:s1manual}}{cmd:s1mono} at the manuals' page size, with larger
    text and symbols{p_end}
{synopt:{cmd:s1rcolor}}light on a dark background{p_end}
{synopt:{cmd:economist}}{p_end}
{synopt:{cmd:sj}}{p_end}
{synoptline}

{pstd}
A scheme directive that Stata's {cmd:graph} consumes is consumed by
{cmd:dash}, in the place Stata consumes it, and where Stata draws nothing
{cmd:dash} draws nothing.  The scheme sets:

{phang2}{ul:Regions.}  The background and plot-region colours
    ({cmd:color background}, {cmd:color plotregion}) and the figure
    proportions ({cmd:graphsize x}, {cmd:graphsize y}; see
    {help dash##geometry:Figure proportions}).{p_end}

{phang2}{ul:Series.}  The colour, symbol, line-pattern and line-width
    cycles ({cmd:p1} to {cmd:p15}), the marker colour where a scheme
    declares a {cmd:color p}{it:#}{cmd:mark} apart from {cmd:p}{it:#}, the
    marker size ({cmd:symbolsize p}), the fill intensities, and a colour
    opacity the scheme declares ({cmd:sttrans}'s {cmd:%20}), which is
    carried into the scatter, connected, line, bar, area and histogram
    layers in both modes and wins over the alpha {cmd:dash} otherwise
    derives from the intensities; the range, spike, fit, band, density,
    function and immediate layers take the colour but not yet its opacity;
    your own {cmd:mcolor(}{it:x}{cmd:%}{it:NN}{cmd:)} or {cmd:malpha()}
    still wins over both.{p_end}

{phang2}{ul:Grids.}  A major grid is drawn on an axis only where the
    scheme says so ({cmd:yesno draw_major_hgrid} for the x axis,
    {cmd:draw_major_vgrid} for the y axis), in {cmd:color major_grid} at
    {cmd:linewidth major_grid}; a minor grid only where
    {cmd:draw_minor_hgrid} or {cmd:draw_minor_vgrid} says so, which no
    shipped scheme does.  So {cmd:s1color}, {cmd:s1mono}, {cmd:s1rcolor}
    and {cmd:stmono1} draw no grid at all, as in Stata.  A grid that
    {cmd:xlabel(, grid)} or {cmd:ylabel(, grid)} turns on is drawn in the
    scheme's grid colour.{p_end}

{phang2}{ul:Text.}  Each piece of text takes the size and colour of the
    Stata textbox style that draws it: {cmd:title()} is {cmd:heading},
    {cmd:subtitle()} is {cmd:subheading}, {cmd:caption()} is {cmd:body},
    {cmd:note()} is {cmd:small_body} (Stata's note textbox does not use
    {cmd:gsize note}, and neither does {cmd:dash}), axis titles are
    {cmd:axis_title}, tick labels {cmd:tick_label} and legend entries
    {cmd:key_label}.  The dashboard's own title and subtitle use
    {cmd:heading} and {cmd:subheading}.  Under {cmd:s1rcolor} every one of
    them is white on black; under {cmd:economist} the title is drawn
    larger than the subtitle, as its {cmd:gsize heading 6.0} asks.{p_end}

{phang2}{ul:Legend.}  Its background and border ({cmd:color legend},
    {cmd:color legend_line}), its text ({cmd:key_label}) and, when the
    graph gives no {cmd:legend(}{it:position}{cmd:)},
    {cmd:legend(position())} or {cmd:legend(ring())}, its placement and
    columns from {cmd:clockdir legend_position} and
    {cmd:numstyle legend_cols}: below the plot in two columns under
    {cmd:s2color}, to the right in one under {cmd:stcolor}, above in three
    under {cmd:economist}.  {cmd:legend(cols())} and {cmd:legend(rows())}
    still win.{p_end}

{phang2}{ul:KPI cards.}  A card is drawn as the scheme's legend box: its
    background is {cmd:color legend}, its border {cmd:color legend_line}
    and its text {cmd:color text}, so a card under {cmd:economist} is the
    scheme's {cmd:#c6d3df} and a card under {cmd:s1rcolor} is black with
    white text.  A KPI's own {cmd:bgcolor()} and {cmd:color()} still
    win.{p_end}

{pstd}
{ul:Units.}  Sizes are converted on Stata's own scale.  A {cmd:gsize} or
{cmd:symbolsize} number is a relative size, 100 being the smaller dimension
of the graph, and is drawn as it would be on Stata's four-inch reference
graph: {cmd:medium} text is 3.8194, which is 11 point, so one unit is 2.88
point, and {cmd:economist}'s {cmd:gsize heading 6.0} is 17.28 point.
Marker sizes follow Stata's {cmd:symbolsize} ladder, which is not the text
ladder: a {cmd:large} marker is 7 point against {cmd:medium}'s 4.4.  A
{cmd:linewidth} number is Stata's own unit, {cmd:medium} being 0.30, so
{cmd:economist}'s {cmd:linewidth p 1.2} draws four times as wide as
{cmd:s2color}'s lines.

{pstd}
An explicit graph option always wins.  The scheme is applied first and your
options after it, so {cmd:bgcolor()}, {cmd:plotregion()}, {cmd:mcolor()},
{cmd:msize()}, {cmd:lwidth()}, {cmd:title(}{it:text}{cmd:, size() color())},
{cmd:legend()}, {cmd:xlabel(, grid)}, {cmd:xlabel(, nogrid)} and the rest
take precedence over whatever the scheme asks for.

{pstd}
{cmd:theme(}{it:name}{cmd:)} is an alias for a scheme, kept for
compatibility: {cmd:default} is {cmd:s2color}, {cmd:clean} is {cmd:s1color},
{cmd:mono} is {cmd:s1mono}, {cmd:dark} is {cmd:s1rcolor}, and
{cmd:economist} and {cmd:sj} name themselves.  {cmd:scheme()} wins if both
are given.

{pstd}
{ul:A scheme of your own.}  To use a scheme {cmd:dash} does not ship, put
its {cmd:.scheme} file in the working directory and name it either by its
base name, {cmd:scheme(mytheme)}, or by its file name,
{cmd:scheme(mytheme.scheme)}.  Both work on every entry point -- a plot
drawn at once with {cmd:dash} {it:plottype}, a {cmd:scheme()} written on
a registered graph or inside a layer's parentheses, {cmd:dash build} and
{cmd:dash serve} -- and the page and every figure take the same file.  A
file in the working directory wins over a shipped scheme of the same
name.  A shipped name may be given with the extension too,
{cmd:scheme(s2color.scheme)}, on every entry point and with no file in
the working directory.  A scheme another package installed into
{cmd:PLUS} is not read from there, deliberately: the letter directories
are shared, so
{cmd:dash} reads only its own translations and the working directory.
Copy the file into the working directory instead.  A name carrying a
directory separator or {cmd:..} is refused.

{pstd}
{ul:A name that resolves to nothing is refused.}  A {cmd:scheme()} that
is neither a shipped scheme, one of the {cmd:theme()} aliases nor a
{cmd:.scheme} file in the working directory is refused before any Python
runs, on every entry point, with r(198):

{phang3}{cmd:. dash build, saving(d.html) scheme(nosuchthing) replace}{p_end}
{phang3}{cmd:dash build: scheme() must be a shipped scheme, a theme, or a .scheme file in the working directory (got: nosuchthing)}{p_end}

{pstd}
and a {cmd:theme()} likewise, naming its six values:
{cmd:dash build: theme() must be one of clean, dark, default, economist, mono, sj (got: nosuchtheme)}.
That is stricter than {cmd:twoway}, which draws {cmd:s2color} with a note
when a scheme is not found, and the same as {cmd:set scheme}, which is
r(111): a dashboard is a file you look at later, so {cmd:dash} will not
save one in a scheme you did not ask for.  The session's own
{cmd:c(scheme)}, inherited when you name none, is the one exception.
When {cmd:dash} cannot translate it -- a third-party scheme, or one of
StataCorp's internal ones such as {cmd:stcolor_meta} -- it says so once,
{cmd:dash: 'X' is not a known theme or scheme; it was inherited from the session (c(scheme)) because no scheme() or theme() was given ...; using s2color},
and draws {cmd:s2color}; never an error, so a session set to a scheme
{cmd:dash} does not know still builds.

{pstd}
{ul:What a scheme file of yours may include.}  StataCorp's schemes are
written as edits on top of an {cmd:#include}d parent, and {cmd:dash}
resolves that chain once, when it extracts its twenty translations, so
each shipped file already carries every directive it needs with every
colour written as hex.  A file of yours is read the same way: an
{cmd:#include} is resolved as {cmd:scheme()} itself is -- a {cmd:.scheme}
file of that name in the working directory first, then one of the twenty
translations {cmd:dash} ships -- never Stata's own
{cmd:scheme-}{it:name}{cmd:.scheme}.  An {cmd:#include} that resolves to
neither (one of StataCorp's internal schemes, such as
{cmd:stcolor_meta}, or a third-party scheme) is skipped in silence, so a
scheme built on one has to state every directive it wants itself.
Colours may be Stata colour names or {cmd:#rrggbb}.

{pstd}
{ul:What the shipped files are.}  Each is a translation in {cmd:dash}'s
own format, not a copy of StataCorp's file and not a drop-in Stata
scheme: about 135 directives (the {cmd:s2mono} family, which declares a
line-plot cycle, about 165) where Stata's {cmd:scheme-s2color.scheme}
has 2060, the {cmd:#include} chain flattened into the file, every colour
resolved to {cmd:#rrggbb} ({cmd:sttrans}'s with the {cmd:%20} opacity
Stata declares kept as {cmd:#rrggbb%20}), and a {cmd:* provenance:}
comment for every
directive saying whether it was transcribed from Stata's file, and from
which directive, or inferred by {cmd:dash} -- the {cmd:p}{it:#}{cmd:line},
{cmd:p}{it:#}{cmd:bar} and {cmd:p}{it:#}{cmd:mark} colours, the marker
symbols, the line patterns and the area intensity, which Stata resolves
through its {cmd:p}{it:#}{cmd:stub} fallback and {cmd:dash} writes out
resolved.  The directives {cmd:dash} does not carry govern what it does
not draw: bar, box, pie, dot and matrix styling, margins and tick
geometry.  {cmd:graph} never reads these files (see below).

{pstd}
{it:Example:}
{phang2}{cmd:. dash build, saving(d.html) scheme(s1rcolor) replace}{p_end}

{pstd}
{ul:Where the shipped schemes live after an install.}  {cmd:net install}
files by basename and extension rather than by the path in the manifest, so
the twenty {cmd:.scheme} files land in the {cmd:PLUS} letter directories --
{cmd:PLUS/s/s2color.scheme}, {cmd:PLUS/e/economist.scheme} and so on -- while
{cmd:dash_render.py} goes to {cmd:PLUS/py/}.  {cmd:dash} looks there for
its own twenty names and for nothing else, so {cmd:scheme()} works the
same from an installed copy as from a source checkout, and a third-party
{cmd:scheme-}{it:name}{cmd:.scheme} in the same directory stays unread.
A {cmd:.scheme} file you put in the working directory still wins over
the shipped one of the same name.

{pstd}
{ul:They are named without Stata's {cmd:scheme-} prefix, deliberately.}
StataCorp's own files are {cmd:scheme-}{it:name}{cmd:.scheme} and
{cmd:dash}'s are plain {it:name}{cmd:.scheme}.  {cmd:set scheme}
{it:name} looks for {cmd:scheme-}{it:name}{cmd:.scheme} first and only then
for {it:name}{cmd:.scheme}, so Stata always finds its own copy and
{cmd:dash}'s translations never change how {cmd:graph} draws.  Renaming them
to {cmd:dash_}{it:name}{cmd:.scheme} would end the chance of a clash with
another package that ships a bare {it:name}{cmd:.scheme}, but
{cmd:scheme(}{it:file}{cmd:.scheme)} is a supported way to name a file, so
the current names are kept and the clash is accepted as a known limitation.


{marker unsupported}
{title:Unsupported Stata twoway options}

{pstd}
The options below are {it:accepted and not honoured}.  None of them is ever
an error, so a command copy-pasted from a do-file always runs -- and every
one that is supplied is named in that command's note, so nothing is dropped
in silence:

{p 12 12 2}{cmd:. dash scatter mpg weight, pstyle(p3) t1title("hi")}{p_end}
{p 12 12 2}{cmd:dash: ignoring unsupported option(s): pstyle() t1title()}{p_end}

{pstd}
This list and that note are generated from the same declarations in
{cmd:dash.ado}, and {cmd:test/test_help_conformance.py} fails if they
disagree in either direction.

{phang2}{ul:Alternative and multi-line titles.}
    {opt t1title(string)}, {opt t2title(string)}, {opt b1title(string)},
    {opt b2title(string)}, {opt l1title(string)}, {opt l2title(string)},
    {opt r1title(string)}, {opt r2title(string)}, {opt title2(string)},
    {opt subtitle2(string)} — {cmd:dash} draws one title per side.  Use
    {cmd:title()}, {cmd:subtitle()}, {cmd:xtitle()} and {cmd:ytitle()}.

{phang2}{ul:Minor ticks and minor labels.}
    {opt xmtick(numlist)}, {opt ymtick(numlist)},
    {opt xmlabel(numlist)}, {opt ymlabel(numlist)} — Bokeh draws one tick
    level per axis.  {cmd:xtick()} and {cmd:xlabel()} are honoured.

{phang2}{ul:Fixed sizing inside a combined graph.}
    {opt fxsize(#)}, {opt fysize(#)}, {opt scale(#)} — these size a panel
    within {cmd:graph combine}, which has no equivalent here: a
    {cmd:dash} figure stretches to the width it is given.  Use
    {cmd:xsize()}, {cmd:ysize()} or {cmd:aspectratio()} to set its
    proportions, and {cmd:layout()} to place it.

{phang2}{ul:Named style stubs.}
    {opt pstyle(name)}, {opt lstyle(name)}, {opt mstyle(name)},
    {opt mlstyle(name)}, {opt mlpattern(patternstyle)},
    {opt mlabwidth(size)}, {opt colorlist(colors)},
    {opt coloruseplegend} — a style stub names a bundle of settings in a
    {cmd:.scheme} file.  {cmd:dash} reads the scheme's own {cmd:p}{it:#}
    cycles directly; set the properties you want with {cmd:mcolor()},
    {cmd:msymbol()}, {cmd:lcolor()}, {cmd:lpattern()} and {cmd:lwidth()}.

{phang2}{ul:Sub-option pass-through.}
    {opt ciopts(...)}, {opt lineopts(...)}, {opt fitopts(...)} — the
    confidence band, the density line and the fitted line each take the
    scheme's own styling.  Their contents are not read.

{phang2}{ul:Bar and dot geometry.}
    {opt at(varname)}, {opt blabel(...)}, {opt horizontal}, {opt vertical},
    {opt sort} — bars are drawn vertically at the x variable's values, and
    {cmd:line} plots are already sorted by x, as in {cmd:twoway}.

{phang2}{ul:Build-time options written on a graph.}
    {opt link(namelist)}, {opt filter(varname, ...)} — these belong to
    {cmd:dash build} and {cmd:dash serve}, where the link group and the
    filter widgets are made.  Written on a graph they are stored and read
    by nothing, so they are named in the note; give them to
    {cmd:dash build}.  Stata's {cmd:nodraw} is not in this list: it is
    honoured, on an immediate render and on {cmd:dash build} alike, by
    keeping the browser window shut.

{phang2}{ul:No Bokeh equivalent.}
    {opt connect(list)} — use the {cmd:connected} plot type.
    {opt cmissing(y|n)} — missing observations are always dropped before
    rendering.
    {opt recast(plottype)} — name the plot type you want directly.
    {opt play(recordingname)} — there is no graph editor to replay.
    {opt text(# # "string")} — use {cmd:note()} or {cmd:caption()}.

{pstd}
Two further notes on the note itself.  It names option {it:names}, never the
values supplied.  And because an unknown option cannot be told apart from a
misspelled supported one, a typo is reported as ignored rather than
rejected: {cmd:titl(x)} abbreviates {cmd:title()} and works, while
{cmd:titel(x)} appears in the note.



{marker dependencies}
{title:Dependencies}

{pstd}
Run {helpb dash_setup} once before using {cmd:dash}.
{cmd:dash_setup} installs and verifies all required software:

{phang2}{ul:Python 3.8+} — linked to Stata via {helpb python}.

{phang2}{ul:Python packages, required} — bokeh≥3.0, numpy≥1.23,
    pandas≥1.5.

{phang2}{ul:Python packages, optional} — none.  Every statistical
    layer is computed with numpy: {cmd:lfitci} and {cmd:mspline} no
    longer use scipy, {cmd:lowess} no longer uses statsmodels, and
    {cmd:qfitci} and {cmd:kdensity} use neither.  An installed scipy or
    statsmodels is neither required nor read, and {helpb dash_setup} no
    longer installs them.

{phang2}{ul:jsonio} — Stata package for JSON serialization of datasets.
    See {helpb jsonio}.


{marker author}
{title:Also see}

{psee}
{helpb dash_setup}, {helpb twoway}, {helpb jsonio}, {helpb python}
