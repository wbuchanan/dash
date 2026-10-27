{smcl}
{* *! version 0.1.0  18oct2026}{...}
{viewerjumpto "Syntax"            "dash##syntax"}{...}
{viewerjumpto "Description"       "dash##description"}{...}
{viewerjumpto "Installation"      "dash##install"}{...}
{viewerjumpto "Plot types"        "dash##plottypes"}{...}
{viewerjumpto "Differences from twoway" "dash##differences"}{...}
{viewerjumpto "Subcommands"       "dash##subcommands"}{...}
{viewerjumpto "Dashboard Options" "dash##dashboard_options"}{...}
{viewerjumpto "Exporting"         "dash##export"}{...}
{viewerjumpto "Accessibility"     "dash##accessibility"}{...}
{viewerjumpto "Stored results"    "dash##results"}{...}
{viewerjumpto "Layout"            "dash##layout"}{...}
{viewerjumpto "Tabs"              "dash##tabs"}{...}
{viewerjumpto "Linking and Brushing" "dash##linking"}{...}
{viewerjumpto "The toolbar"       "dash##toolbar"}{...}
{viewerjumpto "Data tables"       "dash##table"}{...}
{viewerjumpto "Filters"           "dash##filters"}{...}
{viewerjumpto "KPI Cards"         "dash##kpi"}{...}
{viewerjumpto "Graphs from several frames" "dash##frames"}{...}
{viewerjumpto "Image panels"      "dash##image"}{...}
{viewerjumpto "Server Mode"       "dash##server_mode"}{...}
{viewerjumpto "Temporary files"   "dash##tempfiles"}{...}
{viewerjumpto "Resource limits"   "dash##limits"}{...}
{viewerjumpto "Examples"          "dash##examples"}{...}
{viewerjumpto "Faceting with by()" "dash##faceting"}{...}
{viewerjumpto "Marker Label Options" "dash##marker_labels"}{...}
{viewerjumpto "Statistical Layer Options" "dash##smoother_options"}{...}
{viewerjumpto "Weights"           "dash##weights"}{...}
{viewerjumpto "Region Styling Options" "dash##region_options"}{...}
{viewerjumpto "Axis and Display Options" "dash##axis_options"}{...}
{viewerjumpto "Mapping a Variable to Colour" "dash##colorvar"}{...}
{viewerjumpto "Figure proportions" "dash##geometry"}{...}
{viewerjumpto "Marker and Transparency Options" "dash##markers"}{...}
{viewerjumpto "Stata scheme support" "dash##scheme"}{...}
{viewerjumpto "Unsupported Stata twoway options" "dash##unsupported"}{...}
{viewerjumpto "Dependencies"      "dash##dependencies"}{...}
{viewerjumpto "Author"            "dash##author"}{...}
{viewerjumpto "Also see"          "dash##alsosee"}{...}
{vieweralsosee "twoway"              "help twoway"}{...}
{vieweralsosee "scatter"             "help scatter"}{...}
{vieweralsosee "line"                "help line"}{...}
{vieweralsosee "connected"           "help twoway_connected"}{...}
{vieweralsosee "area"                "help twoway_area"}{...}
{vieweralsosee "bar"                 "help twoway_bar"}{...}
{vieweralsosee "spike"               "help twoway_spike"}{...}
{vieweralsosee "lfit"                "help twoway_lfit"}{...}
{vieweralsosee "qfit"                "help twoway_qfit"}{...}
{vieweralsosee "lfitci"              "help twoway_lfitci"}{...}
{vieweralsosee "qfitci"              "help twoway_qfitci"}{...}
{vieweralsosee "lowess"              "help twoway_lowess"}{...}
{vieweralsosee "lpoly"               "help twoway_lpoly"}{...}
{vieweralsosee "fpfit"               "help twoway_fpfit"}{...}
{vieweralsosee "histogram"           "help twoway_histogram"}{...}
{vieweralsosee "kdensity"            "help twoway_kdensity"}{...}
{vieweralsosee "dash_setup"          "help dash_setup"}{...}

{title:Title}

{phang}
{cmd:dash} {hline 2} Interactive HTML dashboards from {cmd:twoway} syntax


{marker syntax}
{title:Syntax}

{pstd}{ul:Single interactive graph (immediate render)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} [{cmd:,} {it:graph_options}
{cmdab:sav:ing}{cmd:(}{it:filepath} [{cmd:,} {cmd:replace} {cmd:asis}]{cmd:)}]

{pstd}{ul:Named graph (accumulate for multi-graph dashboard)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} [{cmd:,} {it:graph_options}
{cmd:name(}{it:identifier} [{cmd:, replace}]{cmd:)}]

{pstd}{ul:KPI card}{p_end}

{p 8 17 2}
{cmd:dash kpi} {it:statistic}{cmd:(}{it:varname}{cmd:)} {ifin} {cmd:,}
{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:nam:e}{cmd:(}{it:identifier} [{cmd:, replace}]{cmd:)}
[{cmdab:fmt:}{cmd:(}{it:format}{cmd:)}
{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}
{cmd:color(}{it:color}{cmd:)}
{cmd:bgcolor(}{it:color}{cmd:)}
{cmdab:upd:ate}{cmd:(}{it:mode}{cmd:)}]

{pstd}{ul:Image panel}{p_end}

{p 8 17 2}
{cmd:dash image using} {it:filename}{cmd:,} {cmd:name(}{it:name}{cmd:)} [{cmd:caption(}{it:text}{cmd:)} {cmd:alt(}{it:text}{cmd:)} {cmd:link(}{it:page}{cmd:.html)}]

{pstd}{ul:Build dashboard (standalone HTML)}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath} [{cmd:,} {cmd:replace} {cmd:asis}]{cmd:)}
[{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}
{cmdab:lay:out}{cmd:(}{it:layout_spec}{cmd:)}
{cmd:link(}{it:namelist} | {cmd:_all}{cmd:)}
{cmdab:br:ush}{cmd:(highlight}|{cmd:filter)}
{cmd:filter(}{it:varname} [{cmd:, type(}{it:filter_type}{cmd:)} {cmd:exclude(}{it:namelist}{cmd:)} {cmd:label(}{it:string}{cmd:)}]{cmd:)}
{cmd:tabs(}{it:tab_spec}{cmd:)}
{cmdab:filterpos:ition}{cmd:(top}|{cmd:left)}
{cmd:theme(}{it:theme_name}{cmd:)}
{cmdab:sch:eme}{cmd:(}{it:schemename}{cmd:)}
{cmd:csv}
{cmdab:nobr:owser}
{cmd:replace}]

{pstd}{ul:Build Bokeh Server app (write .py file, do not block)}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath.py} [{cmd:,} {cmd:replace}]{cmd:)}
{cmd:server}
[{it:other_build_options}]

{pstd}{ul:Launch Bokeh Server (blocking -- press Break to stop)}{p_end}

{p 8 17 2}
{cmd:dash serve}
[{cmd:,}
{cmd:port(}{it:#}{cmd:)}
{cmd:nobrowser}
{cmd:timeout(}{it:#}{cmd:)}
{cmd:maxsessions(}{it:#}{cmd:)}
{cmd:idletimeout(}{it:#}{cmd:)}
[{it:other_build_options}]]

{pstd}{ul:Clear registry}{p_end}

{p 8 17 2}
{cmd:dash clear}

{pstd}{ul:Setup}{p_end}

{p 8 17 2}
{cmd:dash_setup} [{cmd:,} {it:{help dash_setup##options:setup_options}}]

{pstd}
where {it:plot_specs} = {cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)}
[{cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)} ...]
or equivalently using {cmd:||} separators; {it:plottype} is one of those
listed in {help dash##plottypes:Plot types}.  An {it:if} or {it:in} written
outside the parentheses of the {it:plot_specs} -- after them, or before a
{cmd:||} -- applies to every plot, on top of a plot's own, as in
{cmd:twoway}; in the {cmd:||} form without parentheses a qualifier belongs
to the plot it is written in.  A {cmd:||} piece that holds no plot --
{cmd:|| , title("T")} at the end, or {cmd:|| if foreign==1} -- gives its
{it:if}, {it:in} and options to the graph, as in {cmd:twoway}; its options
are graph options only, and a plot option there is refused, r(198).  A
plot written after a parenthesised group,
{cmd:(scatter mpg weight) line mpg weight}, is one more plot, as in
{cmd:twoway}.  {cmd:||} inside one group with no options,
{cmd:(scatter mpg weight || line mpg weight)}, draws both plots, as in
{cmd:twoway}.  A
{it:weight} belongs to a plot, too:
{cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=}{it:varname}{cmd:]} or
{cmd:[pweight=}{it:varname}{cmd:]}, or an expression, as in {cmd:twoway};
see {help dash##weights:Weights}.

{pstd}
{cmd:dash} replaces {cmd:twoway}: type {cmd:dash} where you would type
{cmd:twoway}, as in {cmd:dash (scatter mpg weight) (lfit mpg weight)}.
{cmd:dash twoway scatter mpg weight} is therefore {cmd:twoway twoway scatter mpg weight},
and is refused as {cmd:twoway} refuses that, "twoway is not a twoway plot type",
{cmd:r(198)}; so are {cmd:tw}, {cmd:two}, {cmd:twow}, {cmd:twowa},
{cmd:graph}, {cmd:gr}, {cmd:gra} and {cmd:grap}, in any case, before a
plot, alone or before options.  To use a command copied from a do-file,
replace its {cmd:twoway} (or {cmd:graph twoway}) with {cmd:dash}.
With no plot, {cmd:dash} draws the empty graph {cmd:twoway} draws:
{cmd:dash}, {cmd:dash, title(T)}, {cmd:dash if foreign==1} and
{cmd:dash ||} each register a graph with no plot and no axes, as {cmd:twoway}
draws it; an axis option there is refused as {cmd:twoway} refuses it,
"xlabels(1 2) not allowed, xaxis1 does not exist", {cmd:r(198)}.


{marker description}
{title:Description}

{pstd}
{cmd:dash} accepts the same syntax as {helpb twoway} and produces an
interactive HTML file instead of a static Stata graph window.
The HTML file works offline in any modern browser -- no server, internet
connection, or special software is required.

{pstd}
A dashboard is not a Stata graph: {cmd:graph export}, {cmd:graph save},
{cmd:putdocx} and {cmd:dyndoc} do not see it.  {cmd:dash} stores the path of
the file it wrote in {cmd:r(filename)}; see {help dash##export:Exporting} and
{help dash##results:Stored results}.

{pstd}
For plot types, marker/line/axis options, and {it:if}/{it:in} qualifiers,
{cmd:dash} accepts the same syntax as {helpb twoway}.
See {manhelp twoway G-2:graph twoway} for the full reference.

{pstd}
A qualifier is evaluated against the data in memory when the graph or KPI
is registered, as {cmd:twoway} evaluates it when it draws: an invalid one
stops the command with {cmd:twoway}'s own message and return code, and
nothing is registered.  A variable it abbreviates is written out in full
then.  When the dashboard is built -- {cmd:dash build}, {cmd:dash serve} or
the one-line form -- Stata evaluates each qualifier again, once, against
the data then in memory and in their order, and the dashboard draws exactly
the rows Stata selects: a plot's own {it:if} and {it:in}, the graph's, and
the two together as {cmd:twoway} combines them, and a KPI's.  Everything
Stata allows in a qualifier works as in Stata -- a missing value above
every number ({cmd:if rep78 > 3} keeps the 5 cars with no rating),
subscripts such as {cmd:mpg[_n-1]}, functions such as {cmd:inlist()} and
{cmd:strpos()}, dates, and {cmd:in -10/l}.  In a {cmd:by()} graph, as
{cmd:twoway} does, every qualifier is evaluated with the data sorted on the
{cmd:by()} variables -- a stable sort, so rows that tie keep their order,
and missing values sort last -- and over all the data at once:
{cmd:if _n == 1}, {cmd:in 1/10} and {cmd:mpg[_n-1]} count rows in that
order, and {cmd:_n} does not start again in each panel; the Total panel of
{cmd:by(}{it:varlist}{cmd:, total)} evaluates them in the data's own order.
The data keep their order and are not marked changed.  A qualifier the data no longer
answer -- a variable dropped since the graph was registered -- stops the
build with Stata's own message.  Each distinct qualifier travels to the
dashboard as a column of 0s and 1s (named {cmd:__dashq}{it:#}); no
tooltip, filter or download shows it.  dash names the columns it makes in
Stata -- the qualifier, join-order, time-series and weight columns -- and,
when graphs come from several frames, its copies of variables and value
labels, with a prefix none of the data's names starts with: {cmd:__dash},
or {cmd:__dsh1_}, {cmd:__dsh2_}, ... when a variable (or, on a build, a
value-label set) of a frame the dashboard reads starts with
{cmd:__dash}.  So no column dash makes is a name your data hold, and a
variable named {cmd:__dashq1} is drawn as your data, as {cmd:twoway} draws
it.  The columns the dashboard makes for itself take the same prefix --
its row identity ({cmd:__dash_row__} under {cmd:__dash}), its marker-label,
jitter and colour columns, the alias under which a variable named like one
of its own fields ({cmd:x}, {cmd:y}, {cmd:top}, {cmd:count} ...) reaches
{cmd:hover()} and {cmd:mlabel()}, and the columns that carry {cmd:.a} to
{cmd:.z} -- so a variable named {cmd:__dash_row__} is drawn, shown by
{cmd:hover()}, filtered and downloaded as your data too.  A graph registered in another frame
({cmd:frame} {it:name}{cmd::} {cmd:dash} ...{cmd:, name()}) reads that frame
instead; see {help dash##frames:Graphs from several frames}.

{pstd}
{ul:What a saved page holds.}  A saved dashboard holds, for each variable,
only the observations that some graph, recomputed card or filter selects
with its {it:if} and {it:in}: the rows a layer draws (its graph's qualifier
and its own together), the rows a card that follows a filter or the brush
recomputes over, and the rows a filter acts on.  Nothing of an observation
every qualifier excludes is written into the page, and the page numbers its
own rows, so no gap shows where one was; anyone who opens the file can read
what it holds with View Source.  A card's first value and every fitted line
and smoother are computed over their own rows and only the result is
written, so {cmd:lowess, adjust} and {cmd:lpoly}'s grid still read every
observation in memory, as twoway does, and a {cmd:by()} graph finds its
panels among every observation its graph's qualifier selects.  With
{cmd:csv}, the page holds every observation of every variable it uses.

{pstd}
Two things this rule does not reach: the qualifier, {cmd:by()}-order and
string-fix columns above are generated in the data Stata holds in memory
(dropped again before control returns) -- or, when the data leave no room
for them under {cmd:c(maxvar)}, in a temporary frame beside only the
variables the dashboard exports, and {cmd:r(900)} is given only when even
those leave no room; and a variable named like a
glyph field a plot derives ({cmd:x}, {cmd:y}, {cmd:top}, {cmd:count},
{cmd:density} and the like) draws its own values as a plot variable but is
shadowed by the derived field in {cmd:hover()} and {cmd:mlabel()}.

{pstd}
This help file documents only the features that differ from or extend
{cmd:twoway}.


{marker install}
{title:Installation}

{pstd}
Install {cmd:dash} from its web page with

{phang2}{cmd:net install dash, from("https://wbuchanan.github.io/dash")}{p_end}

{pstd}
and then run, once, the command that checks the Python packages
{cmd:dash} uses and installs the missing ones (see
{help dash##dependencies:Dependencies} and {helpb dash_setup}):

{phang2}{cmd:dash_setup}{p_end}

{marker plottypes}
{title:Plot types}

{pstd}
{cmd:dash} draws the {cmd:twoway} plot types below, each written as in
{cmd:twoway} and abbreviated as {cmd:twoway} allows.  {cmd:twoway} takes
eight of them by a shorter name, or any spelling between it and the full
name -- {cmd:sc} for {cmd:scatter}, {cmd:li} for {cmd:line}, {cmd:con} for
{cmd:connected}, {cmd:hist} for {cmd:histogram}, {cmd:rsc} for
{cmd:rscatter}, {cmd:rl} for {cmd:rline}, {cmd:rcon} for {cmd:rconnected}
and {cmd:fun} for {cmd:function} -- and two by another name, {cmd:mbands}
for {cmd:mband} and {cmd:fn} for {cmd:function}; every other type only by
its full name.  {cmd:dash} takes all of these.  What each draws is
described in {manhelp twoway G-2:graph twoway}; where {cmd:dash} differs,
this file says so under the option concerned.

{synoptset 22}{...}
{synoptline}
{synopt:points, lines, bars}{cmd:scatter}, {cmd:line}, {cmd:connected},
    {cmd:area}, {cmd:bar}, {cmd:spike}, {cmd:dropline}, {cmd:dot}{p_end}
{synopt:immediate}{cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} -- the
    coordinates are written on the command line{p_end}
{synopt:range}{cmd:rarea}, {cmd:rbar}, {cmd:rspike}, {cmd:rcap},
    {cmd:rcapsym}, {cmd:rscatter}, {cmd:rline}, {cmd:rconnected}{p_end}
{synopt:range with a point}{cmd:rpcap}, {cmd:rpspike}{p_end}
{synopt:surface}{cmd:contour}, {cmd:contourline}{p_end}
{synopt:paired coordinates}{cmd:pcspike}, {cmd:pccapsym}, {cmd:pcarrow},
    {cmd:pcbarrow}, {cmd:pcscatter}{p_end}
{synopt:time series}{cmd:tsline}, {cmd:tsrline} -- drawn against the
    time variable {help tsset} set: each variable of {cmd:tsline} is a
    series, {cmd:tsrline} takes two, and neither takes a time variable in
    its varlist{p_end}
{synopt:fits and smooths}{cmd:lfit}, {cmd:qfit}, {cmd:fpfit},
    {cmd:lfitci}, {cmd:qfitci}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly},
    {cmd:lpolyci}, {cmd:mspline}, {cmd:mband}{p_end}
{synopt:distributions}{cmd:histogram}, {cmd:kdensity}{p_end}
{synopt:functions}{cmd:function}{p_end}
{synoptline}

{pstd}
{ul:Arrowheads.}  {cmd:pcarrow}, {cmd:pcbarrow} and {cmd:pcarrowi} draw
their heads as {cmd:twoway}'s {cmd:_gr_arrowhead} draws them, in the saved
page and the served app, at every zoom and after a filter move: two open
strokes from the tip, {cmd:msize()} long (by default the scheme's
{cmd:symbolsize parrow}, {cmd:medium}), stroked in {cmd:mlcolor()} or
{cmd:mcolor()} at {cmd:mlwidth()} (by default the series colour at the
scheme's arrow line width: {cmd:lcolor()} and {cmd:lwidth()} style the
shaft alone, as in {cmd:twoway}); {cmd:pcbarrow} draws one at each end.
The marker labels' gap is measured from the head's size.

{phang2}{opt mangle(anglestyle)} sets the head's half-angle, an
anglestyle name or a number of degrees ({cmd:stdarrow}, 28.64 degrees, by
default); a name that is not an anglestyle is reported and the default
drawn, as {cmd:twoway} notes it.

{phang2}{opt barbsize(size)} sets the barb depth: zero, the default, draws
the two open strokes; any other size draws a closed head filled in
{cmd:mfcolor()} or {cmd:mcolor()} (the series colour by default), its back
point {it:size}*cos({cmd:mangle}) behind the tip.

{phang2}{opt headlabel} puts the marker labels at the second point, the
head, instead of the first.

{pstd}
On the other plot types these three options are named in the note.

{pstd}
A range type takes three variables, {it:y1 y2 x}, and a paired-coordinate
type four, {it:y1 x1 y2 x2}; a fit or smooth takes one {it:y} and one
{it:x}.  Any other count is refused as {cmd:twoway} refuses it, in its
words and with its return code -- {cmd:rscatter mpg weight} is "rscatter
requires 3 variables: mpg weight", r(102) -- before anything is
registered.  A string variable in a plot's varlist is refused the same
way, with {cmd:twoway}'s own {cmd:r(109)} and words, before anything is
registered or drawn -- every plot type above that takes variables, at
every position.  {cmd:colorvar()}, {cmd:mlabel()}, {cmd:hover()} and
{cmd:by()} are not plot variables and still take a string.  So is a
statistical plot whose sample {cmd:twoway} cannot draw: {cmd:lpoly} with no observations in its sample ("no observations",
r(2000)) or one, {cmd:lfit}, {cmd:lfitci} and {cmd:kdensity} with one
("insufficient observations", r(2001)), {cmd:fpfit} and {cmd:fpfitci}
with none its {cmd:if} and {cmd:in} select, {cmd:mspline} and {cmd:mband}
with none and no {cmd:bands()}, and {cmd:histogram} on a dataset with no
observations (r(198)).  Where {cmd:twoway} draws an empty fit with a note
-- {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} or {cmd:qfitci} on no
observations, {cmd:qfit}, {cmd:qfitci}, {cmd:fpfit} or {cmd:fpfitci} on
one -- {cmd:dash} gives the same note, "(note:  regress could not fit
model)" or "(note:  fracpoly could not fit model)", in the saved page and
the served app.  Two observations are fitted: {cmd:qfit}, {cmd:lfitci}
and {cmd:qfitci} draw {cmd:twoway}'s fit with no band, and on an {it:x}
with two values {cmd:qfit} and {cmd:qfitci} fit the term {cmd:regress}
keeps.  A smoother {cmd:twoway} draws empty in silence -- {cmd:lowess} on
fewer than three observations or on an {it:x} that does not vary,
{cmd:lpoly} and {cmd:lpolyci} whose smooth is missing everywhere -- and a
{cmd:scatter}, {cmd:line}, {cmd:area}, {cmd:bar} or other plot of the
observations as they are whose every observation misses one of its
variables,
{cmd:dash} draws in silence too, and {cmd:mspline} and {cmd:mband} on one
observation draw that point.  A {cmd:kdensity} of a variable that does not
vary is drawn as {cmd:twoway} draws it: its {cmd:n()} points at that value
(over {cmd:range()} when given) at a density of 0, or with {cmd:bwidth(#)}
the kernel's height there, in silence, after a filter move too.  A
one-variable plot of a type that takes a {it:y} and an {it:x} is "too few
variables specified", r(102).

{phang}{ul:Orientation.}  {opt horizontal} draws a plot on its side, as
{cmd:twoway} draws it, on {cmd:area}, {cmd:bar}, {cmd:spike},
{cmd:dropline}, {cmd:dot}, {cmd:histogram}, {cmd:kdensity}, the eight
range types, the five paired-coordinate types, {cmd:pci},
{cmd:pcarrowi}, {cmd:function} and {cmd:tsrline}: the {it:x} values run
up the y axis, the {it:y} values across, and the default axis titles and
date labels follow them ({cmd:histogram} {it:var}{cmd:, horizontal}
titles y with the variable and x "Density").  {opt vertical}, the
default, is taken on the same types except {cmd:kdensity} and
{cmd:function}.  {cmd:yaxis(2)} and {cmd:xaxis(2)} stay where they are
(a sideways layer's {it:x} values on {cmd:yaxis(2)} are on the right),
and marker labels keep their clock positions.  Either flag on a type
that does not take it is refused, "option horizontal not allowed",
r(198), judged after {cmd:recast()}; the two together are "may not
combine options horizontal and vertical", r(198).

{pstd}
{ul:Time-series operators.}  A plot variable may carry {cmd:L.}, {cmd:F.},
{cmd:D.} and {cmd:S.}, their combinations and {cmd:L(1/2).}, wherever
{cmd:twoway} takes them: {cmd:scatter}, {cmd:line}, {cmd:connected},
{cmd:area}, {cmd:bar}, {cmd:spike}, {cmd:dropline}, {cmd:dot}, {cmd:lfit},
{cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}, {cmd:mspline}, {cmd:mband}, the
eight range types, the five paired-coordinate types, {cmd:tsline} and
{cmd:tsrline}.  {cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly},
{cmd:lpolyci}, {cmd:histogram} and {cmd:kdensity} refuse them as
{cmd:twoway} does, "factor-variable and time-series operators not
allowed", r(101).  Each series is computed by Stata when the graph is
drawn or the dashboard built, under the {help tsset} then in force and
over every observation, so an {it:if}, an {it:in} and a filter select rows
of it and never recompute it.  It is stored as {cmd:tsrevar} stores it,
with the variable's display format and value labels: a {cmd:D.} of a date
is drawn as a date, as {cmd:twoway} draws it.  Titles, keys and tooltips
read {cmd:twoway}'s text: the variable's label, a comma and the operators
("Closing price, D"), or the expression when the variable has no label.
Without {cmd:tsset} an operator is refused "time variable not set",
r(111); on a string variable "may not use time-series operators on string
variables", r(109); a factor variable is "factor-variable operators not
allowed", r(101); and data not sorted by the time variable are "not
sorted", r(5).  In an option's variable an operator is refused as
{cmd:twoway} refuses it, with or without {cmd:tsset}: {cmd:mlabel(L.make)}
"variable L not found", r(111); {cmd:colorvar(L.mpg)} and
{cmd:by(L.foreign)} "factor-variable and time-series operators not
allowed", r(101); {cmd:mlabvposition(L.pos)} "L.pos invalid name", r(198).
Factor-variable notation is refused the same way: {cmd:by(i.foreign)} and
{cmd:colorvar(c.price)} "factor-variable and time-series operators not
allowed", r(101), a {cmd:#} "interactions not allowed", r(101), and
{cmd:mlabel(i.foreign)} "variable i not found", r(111); {cmd:mlabel(45)}
is "45 invalid name" and {cmd:mlabel(%9.1f)} "invalid '%'", r(198).
In a weight, {cmd:[aw=L.price]}, it is computed as in a plot variable.
{cmd:by()} with an operated plot variable in any layer is
"not sorted", r(5), as in {cmd:twoway}, and {cmd:dash} adds how to
generate the variable first.  A bare {cmd:sort} with an operated {it:x} is
"factor-variable and time-series operators not allowed" and "option
sort() incorrectly specified", r(198), on the types that sort on {it:x}:
{cmd:scatter}, {cmd:line}, {cmd:connected}, {cmd:area}, {cmd:bar},
{cmd:spike}, {cmd:dropline}, {cmd:dot}, {cmd:mspline}, {cmd:mband} and the
eight range types.  The column of the CSV download is headed by the
expression, {cmd:D.close}.

{phang2}{cmd:. sysuse sp500, clear}{p_end}
{phang2}{cmd:. tsset date}{p_end}
{phang2}{cmd:. dash line D.close date}{p_end}

{pstd}
{ul:Join order.}  {cmd:line}, {cmd:connected}, {cmd:area}, {cmd:rline},
{cmd:rarea} and {cmd:rconnected} join their points in the order of the
data, as {cmd:twoway} does.  {cmd:sort} joins them in the order of {it:x},
and {cmd:sort(}{it:varlist}{cmd:)} in the order of {it:varlist}, whether or
not {cmd:sort} is also given; of several copies the last one that is not
empty counts.  Points whose keys tie keep the order of the data
({cmd:twoway}'s order among them changes from one run to the next).
Strings sort byte by byte, and {cmd:.} before {cmd:.a} before {cmd:.b}, as
Stata's {cmd:sort} sorts them.  {cmd:tsline} and {cmd:tsrline} join in time
order and ignore both.  On data not sorted by {it:x} an area follows the
data and crosses itself where {cmd:twoway}'s does; add {cmd:sort} for a
picture along {it:x}.  Each bound of {cmd:rline} and {cmd:tsrline} keeps
its own missing values: it is drawn through the observations where that
bound is present, as {cmd:twoway} draws it; {cmd:rarea} keeps an
observation missing one bound as {cmd:twoway}'s polygon does, its edge
running straight across the gap from the bound's neighbours (one at the
first or last such observation is left out).  A fractional period value
({cmd:%tm} 745.5) is drawn at its fraction toward the next period and
shown as the period that holds it, as {cmd:twoway} draws and shows it.  {cmd:rarea} is outlined in the
scheme's area line style -- its plot colour at the medium line width,
under {cmd:s2color} navy as wide as {cmd:line}'s -- along its two bounds,
which {cmd:alcolor()}, {cmd:alwidth()}, {cmd:alpattern()}, {cmd:lcolor()}
and {cmd:color()} restyle; the short edges {cmd:twoway} also strokes
where the area closes at its first and last {it:x} are not drawn.  An
{cmd:area} is outlined whole, as {cmd:twoway} strokes its polygon: along
its top, its base and the two short edges at its first and last points
(under {cmd:nodropbase}, along the chord that closes it), in the scheme's
area line colour, width and pattern, which {cmd:color()}, {cmd:lcolor()},
{cmd:lwidth()}, {cmd:lpattern()} and the named line styles restyle; a
{cmd:cmissing(n)} gap breaks it where it breaks the fill, and its legend
key is the outlined fill.  A malformed name in {cmd:sort()} is
refused on every plot type -- {cmd:sort(x*)} is "* invalid name",
r(198) -- and a name that is no usable variable on the plot types that
draw observations: {cmd:sort(nosuch)} on {cmd:line} is "variable nosuch not
found" and "option sort() incorrectly specified", r(198), in {cmd:twoway}'s
words, and so are more than ten names.  The {cmd:sort()} variables are
never written to the dashboard: their order travels as a rank column,
{cmd:__dashs}{it:#}, that no tooltip, filter or download shows.

{pstd}
{ul:Connecting and missing values.}  {cmd:connect()} and {cmd:cmissing()}
are drawn as {cmd:twoway} draws them, on {cmd:line}, {cmd:connected},
{cmd:tsline}, {cmd:rline}, {cmd:rconnected}, {cmd:tsrline},
{cmd:scatteri}, the fits and smooths and the fit line of the four
{cmd:ci} types, in the saved page and the served app, before and after
a filter move.  A {cmd:scatter} given {cmd:connect()} is {cmd:twoway}'s
{cmd:connected} plot: its line is drawn, and {cmd:clcolor()},
{cmd:clpattern()}, {cmd:clwidth()} and {cmd:sort} are honoured on it.
{cmd:l} (or {cmd:direct}) joins the points in order; {cmd:L} (or
{cmd:ascending}) also breaks the line wherever {it:x} drops (a tie
joins); {cmd:J} (or {cmd:stairstep}) steps across, then up or down;
{cmd:stepstair} steps up or down, then across; and {cmd:i} (or
{cmd:none}) draws no line and keeps the key.  The spellings are
{cmd:twoway}'s, case and all ({cmd:L} is not {cmd:l}); a name
{cmd:twoway} does not know is drawn direct, after {cmd:twoway}'s note.
Every point keeps its tooltip on a stepped line, and a hidden line has
none.  {cmd:cmissing(n)} breaks the line at each observation missing
{it:x} or {it:y} (each bound of a range plot at its own), and
{cmd:cmissing(y)}, the default, joins across it; {cmd:function} joins
across a region where its expression is missing, as {cmd:twoway} does,
and breaks there under {cmd:cmissing(n)}.  Across several {it:y} both
are style lists ({cmd:c(l J)}, {cmd:c(. l)}, {cmd:cmissing(n ..)}),
{cmd:cmissings()} is a copy of {cmd:cmissing()}, and of several copies
the last counts.  A misplaced {cmd:..} is refused, r(198), and a
{cmd:cmissing()} value that is neither yes nor no is refused, r(101),
where {cmd:twoway} draws a connecting line, in {cmd:twoway}'s words.
{cmd:cmissing(n)} splits an {cmd:area} or {cmd:rarea} where it splits a
line: one filled region per run of observations present in {it:x} and
the {it:y}(s), as {cmd:twoway} closes one polygon per run.  It breaks
the line of the fits and smooths where their own result is missing, as
{cmd:twoway}'s does: {cmd:lowess}, {cmd:fpfit} and {cmd:fpfitci} at an
observation that has {it:x} and no {it:y}, {cmd:lpoly} and
{cmd:lpolyci} at a grid point with no neighbour, the band of the
{cmd:ci} types with its line.  {cmd:area} ignores {cmd:connect()}, as
{cmd:twoway} does; {cmd:rarea} draws both bounds by it ({cmd:J} steps
each bound, and the step toward an observation missing a bound is drawn
when a present one follows it, as in {cmd:twoway}).  After a filter
move both modes split the fill, and break a {cmd:lowess} line, where the
rows the filter keeps are missing, and draw {cmd:rarea}'s steps between
the rows it keeps.

{phang2}{opt cmissings(y|n ...)} is {cmd:twoway}'s other spelling of
{cmd:cmissing()}, and is read as it.

{pstd}
With {cmd:by()} {cmd:twoway} answers panel by panel, and so does
{cmd:dash}.  A graph with no panel -- no observation its qualifier
selects, or every {cmd:by()} value missing -- is "nothing to graph",
r(198).  In a panel whose observations its {cmd:if} and {cmd:in} select
none of, {cmd:fpfit} and {cmd:fpfitci}, and {cmd:mspline} and {cmd:mband}
with no {cmd:bands()}, are refused as above.  A panel in which
{cmd:lpoly} or {cmd:lpolyci} has one observation or none, or {cmd:lfit},
{cmd:lfitci} or {cmd:kdensity} has one, is left out of the graph, as
{cmd:twoway} leaves it out -- after {cmd:regress}'s note and
"insufficient observations" for {cmd:lfit} and {cmd:lfitci} -- and a
graph whose every panel is left out is "nothing to graph".  Every other
panel is drawn, with the notes above.  A {cmd:by()} given in any {cmd:||}
segment or plot group is the graph's, and every plot, before or after it,
is answered panel by panel.  The Total panel of {cmd:by(}{it:varlist}{cmd:,}
{cmd:total)} is one more panel, answered as the others are: it is left
out on the same counts, and a graph that keeps it is not "nothing to
graph".

{pstd}
{ul:Case.}  {cmd:dash} takes no plot-type name shorter than {cmd:twoway}'s:
{cmd:ar}, {cmd:lfi} or {cmd:kde} is refused, "{it:word} is not a twoway plot
type", {cmd:r(198)}, as {cmd:twoway} refuses it.  A plot type is read in
lower case, as {cmd:twoway}'s abbreviations are: {cmd:SC}, {cmd:Hist} and
{cmd:Scatter} are refused, "{it:word} is not a twoway plot type",
{cmd:r(198)}.

{pstd}
{ul:pccapsym.}  {cmd:pccapsym} draws each spike with the same marker at
both ends: the line options style the spike, the marker options the
markers, and {cmd:mlabel()} labels the first point.

{pstd}
{ul:rpcap and rpspike.}  Four variables {it:y1 y2 y3 x}: a spike from
{it:y1} to {it:y2} at {it:x}, caps as wide as the marker ({cmd:rpcap}),
and the marker at {it:y3}; {opt msize()} sizes caps and marker together;
the y axis spans all three, and its title is the three variables' labels
joined by {cmd:/} unless they are the same; {cmd:horizontal} turns the
layer.  Drawn in both modes and redrawn from the kept rows after a filter
move.  Two, three or five variables are refused as {cmd:twoway} refuses
them: "you must specify four variables with twoway rpcap", {cmd:r(102)}
or {cmd:r(103)}.

{pstd}
{ul:contour and contourline.}  Three variables {it:z y x}.  The surface is
{cmd:twoway}'s: a thin-plate spline (kernel r^2 log r with a linear trend)
or Shepard's inverse-distance-squared weights over the grid of the
distinct {it:x} by the distinct {it:y}, {opt interp(none)} drawing the
observed cells only; cuts from {opt ccuts()}, {opt levels(#)} with
{opt minmax}, else the z axis's labels ({opt zlabel()}, five by default),
the first and last dropped; colours from {opt crule()} between
{opt scolor()} and {opt ecolor()}, the scheme's rule and ends by default,
or from {opt ccolors()}; the colour key ticked as {cmd:twoway}'s z axis
and placed by {opt clegend()}.  {cmd:contourline} draws black lines at the
cuts, or the levels' colours under {opt colorlines} or {opt ccolors()}
with {opt clwidths()} under {opt colorlines}; {cmd:horizontal} turns
either.  A second {cmd:contour}, or a second {cmd:contourline}, in one
graph is refused as {cmd:twoway} refuses it, {cmd:r(198)}; so are
{opt ccuts()} with {opt levels()}, a weight, and the options on other
plot types.  {it:Differences from twoway:} at a repeated ({it:x}, {it:y})
{cmd:dash} keeps the smallest {it:z} under every {opt interp()};
{cmd:twoway} does so under {opt interp(none)} and otherwise keeps one that
follows {cmd:set sortseed} (measured: rows (2,2,4) and (2,2,5) give the
node 4 or 5 under seeds 1 to 5).  The surface is exact up to 1,000
distinct points; above that a seeded subsample of 1,000 is fitted and
drawn on a 100 x 100 grid over the data's range, and a note says so.  The
polygons are cut by a different algorithm from {cmd:twoway}'s, so their
vertices differ while the level sets agree.  The served app recomputes the
layer after a filter move, and a saved page recomputes the layer after a
filter move up to 1,000 distinct points; above that it is marked (grid
unfiltered), as is any layer the page cannot recompute.  After a move the
cuts are {cmd:twoway}'s for the rows kept (the z axis's ticks or
{opt levels()} over their z range), the bands are coloured for their new
count, and the colour key takes the new cuts and ticks within the span it
was first drawn with, where {cmd:twoway} would draw the key over the kept
rows' z range.  The saved page
cuts the polygons with dash's own routine, so their vertices differ from
{cmd:twoway}'s while the level sets agree, and a node exactly on a cut may
join rings differently from the served app's.  {opt heatmap} draws
each node's cell -- to the midpoints between nodes, the grid's ends at
its edge -- in its level's colour in place of the bands;
{opt outlines} strokes the bands' boundaries black at twice a medium
line; {opt alpattern()} dashes the boundaries' hairline in their
levels' colours, and {opt sort} draws what {cmd:alpattern(dash)} draws,
as {cmd:twoway} draws each; all four are redrawn after a move.
{cmd:contourline}'s legend keys are named in a note and not drawn,
which
{opt clabels()} and {opt format()} label.  {opt lev()} through
{opt level()} are {opt levels()} here, as {cmd:twoway} reads them, and
{opt le()} is refused, as {cmd:twoway} refuses it; {opt levels()} above
500, and more than 499 values in {opt ccuts()}, are refused, as
{cmd:twoway} refuses them when it draws
({cmd:contour level must be between 0 and 500});
{opt interp()} ({opt i()} and longer), {opt clwidths()} ({opt clw()}),
{opt clpatterns()} ({opt clp()}) and {opt colorlines} ({opt colorl}) take
{cmd:twoway}'s shorter spellings on these two types.

{pstd}
{marker contour_unknown}{ul:An option contour does not know.}  With
{opt levels()}, {cmd:twoway}'s {cmd:contour} and {cmd:contourline} take an
option they do not know and draw nothing of it ({cmd:levels(10) bogus(1)}
draws); without {opt levels()} they refuse it, "option bogus() not
allowed", {cmd:r(198)}.  {cmd:dash} refuses it with or without
{opt levels()}, in those words, as {cmd:twoway} refuses an unknown option
on every other plot type.

{phang2}{opt heatmap} -- {cmd:contour}: the surface's cells in their
levels' colours in place of the bands, as {cmd:twoway} draws them.{p_end}
{phang2}{opt outlines} -- {cmd:contour}: the bands' boundaries black at
twice a medium line, as {cmd:twoway} draws them.{p_end}

{pstd}
{ul:Bars and range caps.}  {cmd:bar} and {cmd:rbar} draw each bar one unit
of {it:x} wide whatever the spacing of {it:x}, as {cmd:twoway} does, and
{cmd:barwidth(}{it:#}{cmd:)} sets another width in the same units.  On a
date axis the unit is the variable's own: a day for {cmd:%td}, a
millisecond for {cmd:%tc} and {cmd:%tC}, and a week, month, quarter,
half-year or year for {cmd:%tw} to {cmd:%ty}; so monthly data held as
{cmd:%td} dates draws bars a day wide, as in {cmd:twoway}, and
{cmd:barwidth(30)} widens them.  Widths do not change when a filter moves.
{cmd:rbar}'s bars are outlined in their plot colour, as {cmd:twoway}
outlines them; {cmd:blcolor()} and {cmd:color()} restyle the outline.
With {cmd:mwidth}, {cmd:rbar} draws each bar as wide as a marker of its
{cmd:msize()} (the scheme's symbol size by default), in screen units,
as {cmd:twoway}'s {cmd:rbar} {cmd:mwidth} draws, whatever the spacing
of {it:x}; {cmd:barwidth()} beside it is read as that marker size, as in
{cmd:twoway}.  Without {cmd:mwidth}, {cmd:msize()} is taken in silence,
as {cmd:twoway} draws nothing of it.  {cmd:histogram} with {cmd:mwidth}
draws each bar as wide as a marker of size {cmd:barwidth()} -- the bin
width by default -- centred on the bin's start, as {cmd:twoway} draws it
({cmd:msize()} is not read), and turned by {cmd:horizontal} each bar
is as tall, centred on its bin's start.
{cmd:rcap} draws its caps as long as a marker of its {cmd:msize()} is wide,
the scheme's symbol size by default, in screen units.  {cmd:rcapsym} draws
no caps, only its spike and a marker at each end, at the scheme's symbol
size unless {cmd:msize()} says otherwise.  {cmd:barwidth()} on {cmd:rcap}
or {cmd:rcapsym} is refused, r(198), as {cmd:twoway} refuses it.

{pstd}
{ul:Where bars stand.}  {cmd:bar}, {cmd:spike}, {cmd:dropline} and
{cmd:area} stand where {cmd:twoway} stands them: on 0 when the axis holds
it, otherwise on the end of the axis nearest 0; see {opt base(#)} under
Statistical Layer Options.

{pstd}
{ul:Immediate values.}  {cmd:scatteri}, {cmd:pci} and {cmd:pcarrowi} read
their values as {cmd:twoway} does: {it:#y #x} for {cmd:scatteri} and
{it:#y1 #x1 #y2 #x2} for {cmd:pci} and {cmd:pcarrowi}, each followed by an
optional clock position in parentheses and then an optional label in
quotes.  A missing value -- {cmd:.} or {cmd:.a} to {cmd:.z} -- draws
nothing, and so does a number past the range of the float {cmd:twoway}
stores it as.  {cmd:dash} refuses, with {cmd:r(198)}, a coordinate that is
not a number, a clock position that is not a number from 0 to 12, and a
list with no whole point, segment or arrow.  A coordinate {it:p}/{it:q}
with {it:p} equal to {it:q} is 1 (0/0 missing), as {cmd:twoway} evaluates
it ({cmd:scatteri 2/2 1} draws at 1, 1), and {it:p} unequal to {it:q} is
refused, as {cmd:twoway} refuses it.
What {cmd:twoway} drops silently at the end of the list -- too little for
another point, segment or arrow, or everything from a {cmd:""} where one's
last number belongs -- {cmd:dash} drops with a note.  A label is drawn at
its point for {cmd:scatteri} and at its arrow's tail for {cmd:pcarrowi},
placed by its clock position, else by {cmd:mlabposition()}, else at 3
o'clock; a clock position that is not a whole number, such as 3.5, is drawn
at 12 o'clock, where {cmd:twoway} draws it, with a note.  {cmd:pci} draws
no labels, as {cmd:twoway pci} draws none, and says so; otherwise it is
drawn as the immediate {cmd:pcspike} that {cmd:twoway pci} is: in
{cmd:pcspike}'s colour and width, with a legend key as {cmd:pcspike} has.
A list with no values at all -- the type alone, or with only an {cmd:if},
an {cmd:in} or a weight -- is refused with {cmd:r(198)}, as {cmd:twoway}
refuses it.  {cmd:if} and {cmd:in} do not reach the values, which are all
drawn, as in {cmd:twoway}; and a list whose every value is missing draws
nothing and says nothing, as {cmd:twoway} does.

{pstd}
{ul:Functions.}  {cmd:function} draws {it:y} = {it:f}({it:x}) over
{cmd:range()}.  Stata evaluates the expression when the graph is
registered, with the generator {cmd:twoway function} itself uses, over
{cmd:twoway}'s points ({cmd:range()} and {cmd:n()}), under your
{cmd:version}, and after every plot's variables and options and the
{cmd:by()} variables are checked, before the graph's other options, as
{cmd:twoway} orders it.  So {cmd:twoway}'s grammar applies: {cmd:^} is
read from left to right ({cmd:2^3^x} is 1 8 64 at x = 0 1 2), a sign
after {cmd:^} takes one operand, {cmd:/} binds tighter than {cmd:*} and
{cmd:-} tighter than {cmd:+}, Stata's constant is {cmd:_pi}, and every
Stata function, estimate ({cmd:_b[]}), scalar and variable may be used.
What {cmd:twoway} refuses is refused with its code and its one line,
{cmd:error in expression:} and the text after the {cmd:=}:
{cmd:pi*x} and {cmd:e*x} are {cmd:r(111)}, {cmd:x**2}, {cmd:x%2}, a
leading {cmd:+} and {cmd:2x} {cmd:r(198)}, an unknown or full-width
function name {cmd:r(133)}, and an expression too long for Stata
{cmd:r(130)}.  A value that is missing in Stata -- outside the
function's domain, such as the square root of a negative number, or too
large to hold, such as {cmd:1/0} -- is drawn as a gap, as {cmd:twoway}
draws it: {cmd:sqrt(x)} over {cmd:range(-1 1)} is drawn from 0 to 1, and
an expression missing everywhere draws nothing, in silence.  With no
expression, {cmd:function} is refused as {cmd:twoway} refuses it:
{cmd:expression required}, {cmd:r(100)}, or after {it:y} {cmd:=},
{cmd:nothing found where expression expected}, {cmd:r(111)}; a bare
{cmd:=} before it ({cmd:function =x}) is {cmd:invalid name},
{cmd:r(198)}.  Under {cmd:by()}, the expression is evaluated once per
panel, in panel order, over the same {cmd:range()}, as {cmd:twoway}
evaluates it, so {cmd:function y = runiform(), by(foreign)} draws
{cmd:twoway}'s different points in each panel.

{pstd}
The points are fixed when the graph is registered, as {cmd:twoway}'s
drawing is fixed when its command runs: a later change to the data or to
the estimates does not move them, and neither does a filter on the page,
saved or served.  Evaluating has {cmd:twoway}'s side effects:
{cmd:runiform()} advances the random-number stream as {cmd:twoway} does,
and data holding at least {cmd:n()} observations are marked changed
({cmd:c(changed)}).  A dashboard spec written by hand, which carries no
points, is drawn by {cmd:dash} itself.  A spec without stored points is
evaluated by dash's own reader of Stata's grammar: {cmd:+ - * / ^}, the
comparisons {cmd:== != ~= > < >= <=}, {cmd:!} and {cmd:~}, {cmd:&} and
{cmd:|}, {cmd:cond()}, {cmd:min()}, {cmd:max()}, {cmd:round()},
{cmd:int()}, {cmd:trunc()}, {cmd:ln()}, {cmd:log()}, {cmd:log10()},
{cmd:exp()}, {cmd:sqrt()}, {cmd:abs()}, {cmd:floor()}, {cmd:ceil()},
{cmd:sin()}, {cmd:cos()}, {cmd:tan()}, {cmd:normal()}, {cmd:normalden()},
{cmd:invnormal()}, {cmd:_pi} and {cmd:c(pi)}, with Stata's missing values
({cmd:.a} to {cmd:.z} kept apart); anything else is named in the note.
Any other function, name or form
draws that layer empty, saved or served, with one note: the layer needs
the points Stata computes when {cmd:dash} registers the graph, and the
note names the first function or name it uses that {cmd:dash} cannot
evaluate ({cmd:invlogit()}, {cmd:pi}), or says that the expression
cannot be read.  Stored points that cannot be read get the same note.
Registering the graph with {cmd:dash} computes its points in Stata, or
refuses the expression as {cmd:twoway} does.

{pstd}
{ul:Graphs that need no data.}  A graph whose plots are all
{cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} or {cmd:function} draws from its
own values, and needs no data in memory, as in {cmd:twoway}: it is drawn
without any, and {cmd:dash build} builds a dashboard of such graphs, saved
or served, exporting no variable.  Every other plot type takes variables,
and is refused without them, as {cmd:twoway} refuses it:
{cmd:varlist required}, {cmd:r(100)}.

{pstd}
{ul:Not a plot type.}  Any word that is not a plot type is refused,
"{it:word} is not a twoway plot type", {cmd:r(198)}, and the message lists
the plot types above.  A plot type cannot be handled as an unknown option
is -- named in a note and drawn around -- because it is what would be
drawn.

{marker added_text}{...}
{pstd}
{ul:Added text.}  {opt text(# # "string" ...)} draws text at data
points, as {cmd:twoway} draws it, in the saved page and the served app and
after every filter move.  Each copy -- after the comma, in a plot group or
in a {cmd:||} segment -- is drawn with its own sub-options, and each point
{it:y x} with at least one line that is not empty is one text, its quoted
strings stacked as lines.  The text is placed in the units of its axes:
on a date axis a number is a date in the variable's units, {opt yaxis(2)},
{opt xaxis(2)} or {opt axes(# #)} draw it on a second axis, and on a log
or reversed axis it is at the transformed point.  A text never widens an
axis, and one whose point is outside the plot region is still drawn.
Under {cmd:by()} each text is drawn in every panel at the panel's text
size.  Drawn: {opt placement()} (every compass name and clock position
{cmd:twoway} takes; an unknown name is noted and drawn east, as
{cmd:twoway} does), {opt justification()}, {opt orientation()}
({cmd:horizontal}, {cmd:vertical}, {cmd:rvertical}, {cmd:rhorizontal}),
{opt size()}, {opt color()}, {opt box} and {opt nobox}, {opt fcolor()}
and {opt bfcolor()}, {opt lcolor()} and {opt blcolor()}, {opt bcolor()},
{opt lwidth()} and {opt blwidth()}, {opt margin()}, {opt alignment()}
({cmd:top} and {cmd:bottom} draw the text 0.15 of its size above
{cmd:middle}'s place and {cmd:baseline} 0.15 below it, as {cmd:twoway}
does) and {opt tstyle()}
(the base size and colour, {cmd:tstyle(heading)} the heading's, which
{opt size()} and {opt color()} still override; an unknown name draws the
default with {cmd:twoway}'s note); the scheme's {cmd:text_option} box
otherwise, its {cmd:vertical_text text_option} the default
{opt alignment()}.  Every other textbox sub-option {cmd:twoway} takes
({opt width()}, {opt height()}, {opt linegap()}, {opt angle()} ...) is
named once in a note and not drawn.  A
{cmd:$}{it:name}, with or without braces around {it:name}, that reaches
{cmd:dash} in a line -- written {cmd:\$name} in a do-file, or passed
through {cmd:macval()} -- is replaced by the global's value when the graph
is registered, as {cmd:twoway} expands it ({cmd:$$f$$} is read inside out,
as Stata reads it), by text only: a global holding {cmd:`=1+1'} is drawn
as written, where {cmd:twoway} evaluates it.  A line whose globals expand
past 4,000 characters is refused, {cmd:text(): expanded text is too long},
{cmd:r(198)}.  Refused with {cmd:r(198)} in {cmd:twoway}'s words:
a point that is not two numbers ({cmd:invalid point, BAD 30}), an axis
pair no plot draws ({cmd:text() option invalid, specified axis pair (2 1)}
{cmd:not in graph}) and a sub-option {cmd:twoway} does not take
({cmd:option nosuch() not allowed}).  The number of texts times the
{cmd:by()} panels is held to {cmd:$dash_max_added_text}
(see {help dash##limits:Resource limits}).  A text is drawn as typed:
its {help dash##graph_text:graph-text markup} is read, and nothing in it
is run.

{phang}{opt ttext(# # "string" ...)} is {opt text()} whose {it:x} may
also be a date literal, quoted or not, read in the x axis's time format as
{cmd:twoway} reads it: the first {cmd:%t} or {cmd:%d} format among the
axis's label, minor label, tick and minor tick formats, each the first
plot's {it:x} variable's format unless that option's {opt format()}
replaces it.  {cmd:tsline y, ttext(12 2001m1 "event")} draws the text at
2001m1 on a monthly axis.  A literal that format cannot read -- a month
on a daily or numeric axis, {cmd:2001m13}, a missing value -- is refused
as {cmd:twoway} refuses it, {cmd:2001m13 is not a number},
{cmd:r(198)}, and a date function, which {cmd:twoway} does not read
there, is an invalid point.  The literal is read as data and never run.


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

{phang2}    {ul:saving() keeps a file that is already there.}  As
    {cmd:dash build} does, the one-line form refuses a file
    {cmd:saving()} names that exists, "file '...' already exists. Use
    replace option to overwrite.", {cmd:r(198)} ({cmd:twoway} says
    {cmd:r(602)}).  Write {cmd:saving(}{it:filepath}{cmd:, replace)}, as
    for {cmd:twoway}, to write over it; a bare {cmd:replace} after the
    comma is {cmd:dash build}'s option only, and on a graph it is refused
    as {cmd:twoway} refuses it, "option replace not allowed",
    {cmd:r(198)}.  A directory in the file's place is
    never written: with {cmd:replace} it is refused with {cmd:r(608)}, as
    {cmd:twoway} refuses it, on the one-line form and {cmd:dash build}
    alike.  A bare {cmd:replace} is refused in every position, beside
    {cmd:saving()} or not; a named graph is replaced by
    {cmd:name(}{it:name}{cmd:, replace)}.
    {cmd:saving()}'s sub-options are {cmd:twoway}'s, {cmd:replace} and
    {cmd:asis}, in full, in lower case and once each, on the one-line form
    and {cmd:dash build} alike; {cmd:asis} is accepted and changes nothing,
    since a saved page is always fixed.  Any other word is refused as
    {cmd:twoway} refuses it, "option bogus not allowed", {cmd:r(198)}, and
    so is a name holding a blank that is not in quotes: write
    {cmd:saving("my file.html")}.  A comma inside the quotes belongs to the
    name, and {cmd:saving(, replace)} writes {cmd:Graph.html}.

{phang2}    {ul:nodraw still writes the page.}  A graph with {cmd:nodraw} and
    {cmd:saving(}{it:filepath}{cmd:, asis)} writes the page to
    {it:filepath} and opens no browser window; {cmd:twoway} refuses the
    same options, "no current graph", {cmd:r(601)}, since {cmd:asis} saves
    a drawn graph and {cmd:nodraw} draws none.

{phang2}    {ul:graph is read only before twoway.}  After {cmd:dash},
    {cmd:graph} is a prefix only when {cmd:twoway} follows it; before any
    other word it is read as a plot type and refused, "unrecognised plot
    type 'graph'", {cmd:r(198)}, where {cmd:graph} followed by a word that
    is not one of its subcommands gives {cmd:r(4023)}.

{phang2}    {ul:Plot-type names in lower case only.}  Capitalised plot-type
    names twoway takes on a case-insensitive file system ({cmd:Scatter})
    are refused; see {help dash##plottypes:Plot types}.

{phang2}    {ul:Graphs and KPI cards share one namespace.}  A name holds one
    item, whichever kind it is, so {cmd:dash kpi} cannot quietly take a name
    a graph already holds and a graph cannot take a KPI's.  Either is
    refused with {cmd:r(198)} unless you write
    {cmd:name(}{it:name}{cmd:, replace)}, which retires whatever held the
    name before.  {cmd:dash clear} empties the registry.

{phang2}    {ul:One name() per command.}  A graph takes one {cmd:name()}.  A
    second -- in another plot group, after a parenthesised command's comma,
    in another {cmd:||} segment or in the same option list, written in
    full or abbreviated ({cmd:nam}), even naming the same graph -- is refused
    as {cmd:twoway} refuses it, with {cmd:option name() not allowed},
    {cmd:r(198)}, and nothing is registered or replaced.  ({cmd:twoway}
    says the graph already exists, {cmd:r(110)}, instead when its first
    {cmd:name()} names a graph it holds without {cmd:replace}; and when
    that first one says {cmd:replace}, it drops the old graph before it
    refuses, which {cmd:dash} does not.)  {cmd:dash kpi} takes one
    {cmd:name()} too.

{phang2}    {ul:What a name may be.}  A name starts with a letter or an
    underscore and holds only letters, digits and underscores: at most 22
    characters for a graph and 18 for a KPI card.  {cmd:dash} keeps each
    item in Stata globals named after it: a graph in
    {cmd:$dash_json_}{it:name} and {cmd:$dash_spec_}{it:name} (and a
    {cmd:function} graph's points in {cmd:$dash_fpts_}{it:name}), a KPI card
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
    registry holds 100 items unless {cmd:$dash_max_graphs} raises the
    limit, to at most 1,000; see {help dash##limits:Resource limits}.

{phang2}    {ul:The registry lives in Stata globals.}  It is kept in
    {cmd:$dash_graph_registry} and a set of {cmd:$dash_*} macros, which is
    what lets {cmd:dash clear} empty it and what lets a later
    {cmd:dash serve} inherit a {cmd:dash build}'s options.  Setting those
    macros by hand is not supported: {cmd:dash} validates what it registers,
    not what you assign afterwards.

{phang2}3.  {ul:New subcommands.}
    {cmd:dash kpi}, {cmd:dash build}, {cmd:dash serve} and {cmd:dash clear}
    have no {cmd:twoway} equivalents.  See
    {help dash##subcommands:Subcommands}.

{phang2}    {ul:Where a graph-level option may be written.}  A
    graph-level option such as {cmd:title()} is honoured wherever
    {cmd:twoway} honours it: after the top-level comma, or inside a plot
    segment, in both the parenthesis and the {cmd:||} forms.  A plot's
    own option is not: after the plot groups' comma {cmd:twoway} takes
    graph options only, and {cmd:(lfit mpg weight), atobs} -- or
    {cmd:mcolor(red)}, {cmd:kernel()}, {cmd:lo} there -- is refused as
    {cmd:twoway} refuses it, even once, {cmd:option atobs not allowed},
    {cmd:r(198)}, naming the first word after the comma {cmd:twoway} does
    not take.  The graph-wide options {cmd:twoway} declares, such as
    {cmd:below} and {cmd:logging}, are taken there, and named in the note.

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash (scatter mpg weight) (line mpg weight), title("G") name(g1)}{p_end}
{phang3}{cmd:. dash (scatter mpg weight, title("A")) (line mpg weight), name(g2)}{p_end}

{phang2}    Both register a titled graph.  When more than one place names the
    same option, or one option list names it twice, {cmd:dash} resolves it
    as {cmd:twoway} does ({manhelp repeated_options G-4:Concept: repeated options}).
    Most options take their last copy: {cmd:mcolor(red) mcolor(blue)} and
    {cmd:mc(red) mcolor(blue)} draw blue, an option written after the
    top-level comma beats one written inside a segment, and among segments
    the last one to name it wins -- including when the last one gives an
    empty text, {cmd:title("")}, which clears it.  Of
    {cmd:sort(}{it:varlist}{cmd:)} the last copy that is not empty counts,
    as in {cmd:twoway}: {cmd:sort(z) sort()} joins in the order of z.
    {cmd:title()} and the
    other titles, the axis labels and ticks, {cmd:legend()},
    {cmd:xscale()}/{cmd:yscale()}, {cmd:by()}, the regions and
    {cmd:xline()}/{cmd:yline()} merge their copies:
    {cmd:title(A) title(, color(red))} is A in red,
    {cmd:xlabel(1 2) xlabel(3, add)} labels 1, 2 and 3, and each copy of
    {cmd:yline()} keeps its own style.  Copies merge sub-option by
    sub-option under {cmd:twoway}'s full name, the last copy winning, so
    {cmd:legend(c(1)) legend(cols(2))} is two columns and
    {cmd:legend(lab(1 "A")) legend(lab(2 "B"))} keeps both labels;
    {cmd:rows()} beats {cmd:cols()} in and across copies, and within one
    copy a word beats its {cmd:no} form ({cmd:legend(on off)} draws the
    legend).
    {cmd:yvarlabel()}, {cmd:xvarlabel()}, {cmd:mlabprefix()},
    {cmd:mlabsuffix()}, {cmd:lalign()}, {cmd:mlabstyle()} and the valued
    options of {cmd:contour} and {cmd:contourline} draw their last copy, as
    {cmd:twoway} draws it; a {cmd:contour} switch given twice
    ({cmd:minmax minmax}) is refused as {cmd:twoway} refuses it.
    An option {cmd:twoway} takes once --
    {cmd:name()}, {cmd:saving()}, {cmd:scheme()}, {cmd:xsize()},
    {cmd:ysize()}, {cmd:aspectratio()}, a bare {cmd:sort},
    {cmd:horizontal}, {cmd:yaxis()}, {cmd:bwidth()} on {cmd:kdensity},
    {cmd:boundary}, {cmd:nodropbase}, {cmd:baroffset()} on {cmd:rbar} --
    given twice is refused as {cmd:twoway} refuses it:
    {cmd:option scheme() not allowed}, {cmd:r(198)}.  So are
    {cmd:atobs} on the fits, {cmd:nofit}, {cmd:fitplot()} and
    {cmd:ciplot()}, which are drawn, the options
    {cmd:dash} names in its note that {cmd:twoway} takes once, and a
    kernel written as an option of its own ({cmd:gaussian}):
    {cmd:clegend()}, {cmd:plegend()}, {cmd:pcycle()} and the other
    {cmd:colorvar()} and graph-wide options {cmd:twoway} declares:
    {cmd:atobs} given twice on {cmd:lfit} is
    {cmd:option atobs not allowed}, {cmd:r(198)}, naming the second copy as
    typed (the {cmd:no} copy of a pair such as {cmd:dropbase} and
    {cmd:nodropbase}, which are one option), and the graph-wide ones
    are refused in a second plot group or {cmd:||} segment too.  Each one
    given once is still named in the note, but for the kernel, which is
    drawn (see {cmd:kernel()}).
    An option written in upper case -- {cmd:ATOBS}, {cmd:MCOLOR(red)},
    {cmd:Title(x)}, and {cmd:dash}'s own {cmd:HOVER()} -- is no option,
    since option names are lower case, and is refused as {cmd:twoway}
    refuses it: {cmd:option MCOLOR() not allowed}, {cmd:r(198)}, naming
    the first word of its option list {cmd:twoway} does not take.

{phang2}4.  {ul:New build-time options.}
    {cmd:link()}, {cmd:filter()}, {cmd:layout()}, and {cmd:theme()} are
    specific to {cmd:dash} and control multi-graph layout and
    interactivity.

{phang2}5.  {ul:Unsupported twoway options.}
    {cmd:dash} accepts every {cmd:twoway} option by name.  A word
    {cmd:twoway} does not take is refused as {cmd:twoway} refuses it --
    {cmd:bogus}, {cmd:xreverse}, {cmd:cl(red)} and {cmd:bargap()} on
    {cmd:scatter} are {cmd:option bogus not allowed}, {cmd:r(198)} -- and so
    is one written in upper case, or a plot's option after the plot groups'
    comma (see {it:Where a graph-level option may be written} under 3.
    above).  {cmd:dash} names the word {cmd:twoway} names: the first of the
    list it does not take, before two kernels, {cmd:mlabfontface()} and a
    graph option given twice ({cmd:gaussian epan2 bogus} is
    {cmd:option bogus not allowed}), and after a plot's option given twice
    before it -- across {cmd:||} segments and plot groups too, every plot's
    own options before any kernel, and the options after the groups' comma
    last.
    So a command copy-pasted from a do-file runs whenever
    {cmd:dash} draws its plot type ({help dash##plottypes:Plot types})
    and can draw the values it is given: a few values {cmd:twoway} accepts, such as
    {cmd:bin(2000)}, are more than {cmd:dash} draws and are refused (see
    {help dash##validation:Option values} below).  Anything {cmd:dash}
    cannot honour is named once per command, in a single note:

{p 12 12 2}{cmd:. sysuse auto, clear}{p_end}
{p 12 12 2}{cmd:. dash scatter mpg weight, afcolor(red)}{p_end}
{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): afcolor())}{p_end}

{phang2}
    {ul:How a note is printed.}  Every note {cmd:dash} prints -- this one,
    and those about a value it draws differently or a layer that drew
    nothing -- is printed as {cmd:twoway} prints its notes: one line,
    {cmd:(note: dash:} ...{cmd:)}, in text colour, shown under
    {cmd:quietly} and {cmd:set output error} and hidden by {cmd:capture}.
    A note is printed once per command however often it arises, never
    names a file or a line of {cmd:dash}'s own code, and is neither hidden
    nor made an error by a Python {cmd:warnings} filter or by
    {cmd:PYTHONWARNINGS}; other packages' Python warnings still follow
    those filters.  The two notes {cmd:dash} gives in {cmd:twoway}'s own
    words, {cmd:(note: regress could not fit model)} (or {cmd:fracpoly}'s)
    and {cmd:(note: scheme} {it:name} {cmd:not found, using s2color)},
    are printed as {cmd:twoway} prints them, as plain text that
    {cmd:quietly} hides.

{phang2}
    The note names option {it:names}, never the values supplied, each as
    {cmd:twoway} names it: {cmd:afcolor()} for one that takes a value,
    {cmd:titling} for one typed without, and {cmd:sort} or {cmd:sort()}
    as it was typed.  A typo
    is refused as {cmd:twoway} refuses it: {cmd:titl(x)} is abbreviated
    {cmd:title()} and works, but {cmd:titel(x)} is
    {cmd:option titel() not allowed}, {cmd:r(198)}.  The full list is in
    {help dash##unsupported:Unsupported Stata twoway options}.  An option
    {cmd:dash} honours on some plot types -- {cmd:kernel()}, {cmd:n()},
    {cmd:level()}, {cmd:bwidth()}, {cmd:bands()}, {cmd:range()},
    {cmd:base()}, {cmd:degree()}, {cmd:bin()}, {cmd:width()},
    {cmd:start()} and {cmd:barwidth()} -- is accepted only on the plot
    types {cmd:twoway} accepts it on and refused on any other, as
    {cmd:twoway} refuses it, with r(198) and {cmd:twoway}'s line
    {err:option kernel() not allowed} (naming the option given): a
    {cmd:kernel()} or {cmd:level()} on a {cmd:scatter}, say.  The per-type
    lists are generated from a measured table
    (scripts/extract_applicability_truth.do); the plot types each option
    applies to are also listed under
    {help dash##smoother_options:Statistical Layer Options}.
    The same holds one level down: a sub-option of {cmd:legend()},
    {cmd:xlabel()}/{cmd:ylabel()}, {cmd:xscale()}/{cmd:yscale()},
    {cmd:xtitle()}/{cmd:ytitle()}, {cmd:title()}, {cmd:subtitle()},
    {cmd:note()}, {cmd:caption()}, {cmd:xline()}/{cmd:yline()} or
    {cmd:filter()} that {cmd:dash} does not implement is named in a
    note, as {cmd:by()}'s are:
    {cmd:(note: dash: legend() sub-option(s) not implemented and ignored: stack)}.
    A sub-option of {cmd:legend()}, of the axis labels and ticks
    ({cmd:xlabel()}, {cmd:ylabel()}, {cmd:xtick()}, {cmd:ytick()},
    {cmd:xmlabel()}, {cmd:ymlabel()}, {cmd:xmtick()}, {cmd:ymtick()},
    {cmd:zlabel()}), of {cmd:xline()}/{cmd:yline()} and of a textbox is
    read as {cmd:twoway}'s own parsers read it: in lower case only, from
    its minimum abbreviation to its full name, in the order
    {cmd:twoway} tries them, so {cmd:legend(c(2) r(1) lab(1 "A") posi(6) s(small))},
    {cmd:ylabel(, labs(small) ang(0) for(%9.1f) nog)} and
    {cmd:xline(5, lc(red) lp(dash) lw(thick))} draw as their full names,
    and a second {cmd:c()} after {cmd:cols()} is {cmd:color()}.  Quoted
    label text is never read as a sub-option.  In {cmd:legend()}, the
    axis labels and ticks and the titles, what {cmd:twoway} refuses is
    refused with its return code and words: a sub-option in capitals
    ({cmd:legend(OFF)}: {cmd:option OFF not allowed}, r(198)), a spelling
    {cmd:twoway} does not accept ({cmd:ylabel(, a(45))}), one given twice
    in one option ({cmd:legend(c(2) cols(1))}), the wrong form
    ({cmd:ylabel(, labs)}: {cmd:option labs incorrectly specified}), a
    bad {cmd:cols()}, {cmd:rows()} or {cmd:holes()}
    ({cmd:legend(c(red))}: {cmd:cols() invalid -- invalid number},
    r(121)), a {cmd:label()} key that is no positive integer, and
    {cmd:ytitle("Y", prefix suffix)}.  {cmd:legend(position(13))}, a
    non-numeric {cmd:ring()} and a non-integer {cmd:order()} word draw the
    default with {cmd:twoway}'s note.  {cmd:legend()}'s words are read left
    to right, as {cmd:twoway} reads them, so {cmd:legend(po(9) top)} is
    {cmd:option po() not allowed}; the words inside
    {cmd:legend(region())} and {cmd:legend(title())} are checked as
    {cmd:twoway} checks them ({cmd:legend(region(xx))}: {cmd:option xx not allowed}),
    and the legend title's {cmd:color()} and {cmd:size()} are drawn.
    {cmd:title("T", prefix suffix)} prints {cmd:twoway}'s line,
    {cmd:option prefix ignored, may not be combined with suffix}, and draws
    the title.  A quoted text that opens with an apostrophe,
    {cmd:title("'90s")}, is drawn; {cmd:twoway} reads its {cmd:"'} as the
    close of a compound quote never opened and stops on what follows, in
    words that depend on it ({cmd:) required}, r(100), for
    {cmd:title("'90s")}, {cmd:xlabel(3000 "'90s")} and
    {cmd:legend(label(1 "'90s"))}; {cmd:type mismatch}, r(109), for others),
    while {cmd:dash} keeps a quote's text whole, so that no text can end a
    quote early and become command words.  {cmd:rows()} wins over
    {cmd:cols()}, and in one copy a word wins over its {cmd:no} form
    ({cmd:on} over {cmd:off}, {cmd:grid} over {cmd:nogrid}).  Repeated
    copies merge sub-option by sub-option under the full name, the last
    copy winning, so {cmd:legend(lab(1 "A")) legend(lab(2 "B"))} keeps
    both labels.
    A textbox sub-option -- of {cmd:title()}, {cmd:subtitle()},
    {cmd:note()}, {cmd:caption()} and {cmd:xtitle()}/{cmd:ytitle()} on
    either axis -- is read under any of Stata's
    spellings, from its minimum abbreviation to its full name:
    {cmd:c(red)} is {cmd:color(red)}, {cmd:s(large)} is
    {cmd:size(large)}, {cmd:a()} is {cmd:alignment()}, {cmd:lst()} is
    {cmd:lstyle()}, {cmd:b} is {cmd:box} and {cmd:nob} is {cmd:nobox}.  {cmd:size()}, {cmd:color()}, {cmd:prefix},
    {cmd:suffix} and, on an axis title, {cmd:axis(1)}/{cmd:axis(2)}
    (minimum {cmd:ax()}, in lower case) are applied; on {cmd:title()},
    {cmd:subtitle()}, {cmd:note()} and {cmd:caption()} the placement,
    box and style sub-options are drawn too (see
    {help dash##textbox_options:Textbox options}); every other
    sub-option is named, never drawn as text.  A lone {cmd:suffix} on an axis title adds its lines after the
    default title, {cmd:prefix} before it.
    An axis title given with empty text -- {cmd:xtitle("")},
    {cmd:ytitle("")} or {cmd:ytitle("", axis(2))} --
    removes that title, as in {cmd:twoway}; an option not given at all
    keeps the default title (see
    {it:Legend keys and default axis titles} under Statistical Layer
    Options).
    An axis title given only sub-options -- {cmd:xtitle(, size(large))},
    {cmd:ytitle(, color(red))}, {cmd:ytitle(, axis(2) size(large))},
    {cmd:ztitle(, size(large))} -- keeps the default title and applies
    them, as in {cmd:twoway}; only empty quotes remove a title, and
    {cmd:ytitle("", suffix)} keeps it.  The first comma outside quotes and
    parentheses that is followed by a sub-option name, another comma or
    nothing opens the sub-options, and empty slots are ignored:
    {cmd:ytitle(A,)} and {cmd:ytitle(A,,)} are {cmd:ytitle(A)}, and
    {cmd:ytitle(,)} keeps the default.
    A weight, {cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=]} or
    {cmd:[pweight=]}, is honoured on the statistical layers that take it
    in {cmd:twoway} and refused, as {cmd:twoway} refuses it, where they do
    not; on {cmd:scatter} and the other marker layers it sizes the
    markers, and on the other glyph layers it is taken and draws nothing
    different, as in {cmd:twoway}; it is never named in the note.  See
    {help dash##weights:Weights}.
    {cmd:scheme()} is not among the options named: {cmd:dash} translates
    Stata's own schemes; {help dash##scheme:Stata scheme support} below says
    what a scheme sets and what {cmd:dash} does not yet carry.

{marker validation}
{phang2}    {ul:Option values.}  A value is refused where {cmd:twoway}
    refuses it, and a word is refused where a number-only option was given
    one that {cmd:twoway} would have swallowed in silence.  A style name
    that {cmd:dash} does not recognise (a marker symbol, a size, a line
    width, a line pattern, an angle, a clock position or a fill
    intensity) is reported once per render and the scheme's default drawn
    (for a fill intensity, full intensity), as {cmd:twoway} does with its
    own "named style not found" note.  An unknown or wrong-case colour is
    drawn black and reported in {cmd:twoway}'s own words, "dash: named
    style {it:name} not found in class color, default attributes used", as
    {cmd:twoway} draws and reports it (see {help dash##colours:Colours}).  A
    refusal uses {cmd:twoway}'s return code and words (its first line),
    printed before any Python runs: {cmd:base(abc)} is r(4026) and
    {cmd:mlabel(make..)} r(101), as in {cmd:twoway}.  Where {cmd:twoway} draws the value and {cmd:dash} cannot,
    the refusal is {cmd:dash}'s own line naming the option and the value,
    r(198):

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash (histogram mpg, bin(2000))}{p_end}
{phang3}{cmd:dash: bin() must be an integer between 1 and 1000 (got: 2000). dash draws up to 1000 bins.}{p_end}

{phang2}    The bounds checked in Stata.  Numbers: {cmd:jitter()} and
    {cmd:jitterseed()} any value, as {cmd:twoway} takes them, a word or a
    negative number drawn as none;
    {cmd:level()} any number on {cmd:lfitci}, {cmd:qfitci} and
    {cmd:fpfitci}, as {cmd:twoway} takes it (no band at 100 or more), and
    10 to 99.99 on {cmd:lpolyci}, as {cmd:twoway}; {cmd:aspectratio()} 0 or
    more; {cmd:base()} any number; {cmd:start()} any number, except that
    on {cmd:histogram} a {cmd:start()} above the variable's minimum is
    refused in {cmd:twoway}'s own words,
    {cmd:option start() may not be larger than minimum of mpg};
    {cmd:barwidth()} any number ({cmd:barwidth(-1)}, {cmd:twoway}'s own
    default, draws the default width, and {cmd:barwidth(0)} bars of no
    width); {cmd:width()} and {cmd:bwidth()} positive, except
    that {cmd:kdensity} takes {cmd:bwidth(0)}, its default rule, and
    {cmd:lowess} any number, one outside 0 to 1 drawn at .8, as
    {cmd:twoway} draws it.  Integers:
    {cmd:yaxis()} and {cmd:xaxis()} 1, 2 or both ({cmd:yaxis(1 2)} draws
    the layer on both axes, a list read as {cmd:twoway} reads it);
    {cmd:degree()} 0 or more, as {cmd:twoway} takes it (above 7 it is
    drawn with a note that the result can differ from Stata's, fitted at
    most at degree 30 and never above the distinct x values less one, and
    on the saved page kept as built and marked after a filter move);
    {cmd:n()} 1 to 10000, 1 to 300 on {cmd:mspline}, and up to 10000 on
    {cmd:mband}, where one below 1 draws its default; {cmd:bin()} 1
    to 1000; {cmd:bands()} 1 to 200;
    an integer written as {cmd:yaxis(2.0)}, {cmd:yaxis(02)},
    {cmd:yaxis(+2)} or {cmd:n(1E3)} reaches the renderer as 2, 2, 2 and
    1000.  A name or a number: {cmd:msize()}, {cmd:mlabsize()},
    {cmd:mlabgap()}, {cmd:mlabposition()} and {cmd:fintensity()} any
    number, and {cmd:msize()}, {cmd:mlabsize()} and {cmd:mlabgap()} also a
    number with a unit ({cmd:4pt}, {cmd:.1in}) or a {cmd:*}{it:#}
    multiplier, and {cmd:msize(1e400)}, a number past the machine's range,
    is read as {cmd:msize(0)}, as {cmd:twoway} draws it; {cmd:lwidth()},
    {cmd:mlwidth()} and {cmd:clwidth()} 0 to
    10000 Stata units, as a number, {it:#}{cmd:rs}, a non-negative
    {it:#}{cmd:pt}, {it:#}{cmd:in} or {it:#}{cmd:cm}, or {cmd:*}{it:#},
    refused with {cmd:twoway}'s message
    {cmd:gm_linewidth must be between 0.000 and 1.0e+04}, followed by
    {cmd:dash}'s line naming the option, and, as {cmd:twoway} holds them,
    {cmd:lwidth()} only on a plot type that draws a line or an outline (on
    {cmd:scatter} only when {cmd:connect()} draws one), {cmd:mlwidth()} only
    where it draws markers, and a {cmd:*}{it:#} multiplier past 10000
    units of the 0.3-unit default line ({cmd:lwidth(*40000)} on
    {cmd:line});
    {cmd:alwidth()} the same, 0 to 10000 on the plot types where {cmd:twoway}
    refuses it outside that range (every type but {cmd:line},
    {cmd:connected}, the fits and smooths without a band, {cmd:kdensity},
    {cmd:function}, {cmd:tsline}, {cmd:scatter}, {cmd:dot},
    {cmd:rscatter} and {cmd:scatteri});
    {cmd:msangle()} -360 to 360 where it draws markers; {cmd:xsize()} and {cmd:ysize()} 1 to
    100; a word that only looks like a number, such as
    {cmd:msize(1e308)}, is refused as {cmd:twoway} refuses it
    ({cmd:invalid syntax}).  A word
    from a list: {cmd:kernel()} in lower case, as {cmd:twoway} reads it
    ({cmd:kernel(GAUSSIAN)} is {cmd:invalid kernel function}), and
    {cmd:theme()} without regard to case.  A scheme name:
    {cmd:scheme()} must be a shipped scheme, a {cmd:theme()} name or a
    scheme Stata finds along the ado-path,
    {cmd:scheme-}{it:name}{cmd:.scheme} or {it:name}{cmd:.scheme},
    wherever it is written (see
    {help dash##scheme:Stata scheme support}).  A list of numbers,
    written as any Stata
    {it:numlist}: {cmd:colorcuts()} one or more;
    {cmd:colorcuts(1(1)5)} reaches the renderer as 1 2 3 4 5.
    {cmd:range()}: two numbers, a {cmd:.} for the data's own end on
    {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and {cmd:qfitci}, or on
    {cmd:kdensity} and {cmd:function} a variable, whose minimum and maximum
    over the plot's sample are used (a string or all-missing one draws
    {cmd:kdensity}'s curve empty, in silence, as {cmd:twoway} does, and
    {cmd:function} "no observations", r(2000)); anything else is refused
    with {cmd:twoway}'s code and words.
    Variables: {cmd:colorvar()} names one, {cmd:mlabel()} one per y (see
    {help dash##stylelists:Style lists}), {cmd:hover()}
    one or more, and {cmd:by()} one or more before its comma; each is
    expanded as {cmd:twoway} expands it, so {cmd:by(for)} means
    {cmd:by(foreign)}; a variable that does not exist is r(111) ({cmd:dash build}
    and {cmd:dash serve} also give r(111) for a {cmd:hover()} variable
    dropped after the graph was registered), and a
    time-series expression such as {cmd:mlabel(L.mpg)} is refused, as
    {cmd:twoway} refuses it.  {cmd:xsize()},
    {cmd:ysize()}, {cmd:aspectratio()}, {cmd:hover()} and {cmd:by()} are
    checked wherever they are written, inside a layer's parentheses or
    after the graph's comma.

{phang2}    Two of those bounds are {cmd:dash}'s own resource limits:
    {cmd:twoway} accepts the value, and {cmd:dash} refuses it, saying so
    in a second sentence of the message: {cmd:bin()} up to 1000, and
    {cmd:n()} up to 10000 (on {cmd:mspline}, 1 to 300 is {cmd:twoway}'s
    own bound); see {help dash##limits:Resource limits}.  The others are
    {cmd:twoway}'s, but for one: {cmd:aspectratio()} below 0, which
    {cmd:twoway} draws as a plot region overflowing the graph, a layout
    defect {cmd:dash} does not copy, so it refuses the value, {cmd:r(198)}.
    {cmd:hover()} is an option {cmd:twoway} does not have (see
    {help dash##dashonly:dash's own options}), so every rule on it is
    {cmd:dash}'s own.  {cmd:bands()} 1 to 200 is {cmd:twoway}'s own bound
    ({cmd:bands must be between 1 and 200}).

{phang2}    {cmd:dash} also refuses some forms {cmd:twoway} reads:
    an element of {cmd:mlabel()} that names several variables, such as
    {cmd:t*} ({cmd:twoway} draws no labels for that y).

{phang2}    These values are refused as {cmd:twoway} refuses them:
    {cmd:kernel(GAUSSIAN)}, {cmd:invalid kernel function}, r(198), the
    next line naming {cmd:kernel(gaussian)}; {cmd:xsize(())} and
    {cmd:ysize(())}, {cmd:option(s) ( ) not allowed}, r(198) (inside a
    style list, {cmd:lwidth(())} or {cmd:msize(())}, likewise; see
    {help dash##stylelists:Style lists}); and a string {cmd:colorvar()},
    r(7).  An unknown
    {cmd:scheme()} is refused where {cmd:twoway} draws {cmd:s2color} with
    a note, because a saved dashboard in the wrong scheme is not a note
    you see, and so is an unknown {cmd:theme()}, an option {cmd:twoway}
    does not have; {help dash##scheme:Stata scheme support} says more.

{phang2}    A switch that belongs to one plot type is refused on every
    other, as {cmd:twoway} refuses it, with r(198): {cmd:discrete},
    {cmd:density}, {cmd:fraction}, {cmd:frequency} and {cmd:percent} on
    {cmd:histogram}; {cmd:stdp}, {cmd:stdf} and {cmd:stdr} on
    {cmd:lfitci} and {cmd:qfitci}; {cmd:mean}, {cmd:noweight},
    {cmd:adjust} and {cmd:logit} on {cmd:lowess}.  Two of {cmd:stdp},
    {cmd:stdf} and {cmd:stdr} together ({cmd:may not combine}) and
    {cmd:discrete} with {cmd:bin()} are refused the same way.  A weight
    the plot type does not take is r(101), as in {cmd:twoway}; see
    {help dash##weights:Weights}.

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash (scatter mpg weight, discrete)}{p_end}
{phang3}{cmd:option discrete not allowed}{p_end}

{phang2}    Colours (but for a comma), {cmd:msymbol()}, {cmd:lpattern()} and
    the sub-options of the structured options are not checked in Stata.  An unknown style
    inside one ({cmd:title(T, size(bogus))}) gets a note and the default
    in {cmd:twoway} and in {cmd:dash} alike; so does a symbol or pattern
    name {cmd:twoway} does not know ({cmd:msymbol(star)},
    {cmd:msymbol(CIRCLE)}, {cmd:lpattern(Dash)}: names are
    case-sensitive).  A line pattern is a name or a formula in double
    quotes ({cmd:lpattern("-.")}), drawn at {cmd:twoway}'s lengths, which
    follow the graph's size and not the line's width (to the whole
    pixel); a formula in a scheme is drawn solid, and {cmd:mlpattern()}
    leaves the marker's outline solid, as {cmd:twoway} draws them.  An unknown sub-option word
    of {cmd:legend()} is refused as {cmd:twoway} refuses it
    ({cmd:legend(garbage)}: {cmd:option garbage not allowed}, r(198)),
    and so is one of {cmd:xscale()} or {cmd:yscale()}
    ({cmd:xscale(bogus)}, {cmd:yscale(OFF)}: {cmd:option bogus not allowed}).  A colour written with commas in a plot colour option,
    {cmd:mcolor(255,0,0)}, is refused as {cmd:twoway} refuses it,
    {cmd:invalid '0'}, r(198).  {cmd:twoway} reads such a colour as its
    parts between commas, every second of which must be blank
    ({cmd:mcolor(red,)} is {cmd:invalid 'editcopy'}, {cmd:mcolor(1,,2,3)}
    {cmd:invalid '3'}), in each style-list element a y uses:
    {cmd:mcolor(255 0,0)} on one y is the element {cmd:255}, drawn black
    with the note, and on two y {cmd:invalid '0'}; a form it takes is drawn
    as its other parts joined by blanks, {cmd:mcolor(1,,2)} as {cmd:1 2}
    and {cmd:mcolor(255,,0,,0)} red, and so it is in {cmd:dash}.  A triplet
    is written with blanks and quoted,
    {cmd:mcolor("255 0 0")}, as in {cmd:twoway} (see
    {help dash##stylelists:Style lists}).  Inside a colour sub-option of
    {cmd:title()}, {cmd:subtitle()}, {cmd:note()}, {cmd:caption()},
    {cmd:xline()}, {cmd:yline()}, {cmd:xlabel()}, {cmd:ylabel()},
    {cmd:plotregion()}, {cmd:graphregion()} and {cmd:legend()}
    ({cmd:title(T, color("1,2,3"))}) such a colour is read the same way,
    the whole value at once, and refused as {cmd:twoway} refuses it,
    {cmd:invalid '2'}, r(198).  A quoted colour with a comma glued after
    it, {cmd:mcolor("red",blue)}, is the quoted colour and then
    {cmd:,blue}, as {cmd:twoway} reads it: drawn red on one y, and
    {cmd:invalid 'blue'} on two.  An intensity past the
    darkest a colour can go is drawn by a rule {cmd:twoway} does not
    always follow: {cmd:mcolor(navy*52)} is #010304 in {cmd:twoway} and
    #010102 in {cmd:dash}.

{phang2}    {marker stylelists}{ul:Style lists.}  A style option given a
    list styles the y variables of an expanded varlist in turn, as
    {cmd:twoway}'s {help stylelists:stylelists} do:
    {cmd:scatter mpg turn weight, mcolor(red blue) msymbol(O T)} draws
    {cmd:mpg} in red circles and {cmd:turn} in blue triangles.  {cmd:.}
    leaves that y at its default, {cmd:=} repeats the element before it
    ({cmd:.} when it comes first), and {cmd:..} or {cmd:...}, written alone
    or at the end of an element, repeats the element before it to the last
    y.  A list shorter than the y variables is padded with {cmd:.}, so a
    lone value styles only the first y
    ({cmd:line mpg turn weight, lwidth(thick)} thickens {cmd:mpg}'s line
    alone), and elements past the last y are ignored, values and all.  A
    plot type that draws one y uses the first element.  A quoted element is
    one element: an RGB colour is quoted, {cmd:mcolor("255 0 0")}, because
    {cmd:mcolor(255 0 0)} is a list of three colours, as in {cmd:twoway}. 
    {cmd:..} or {cmd:...} anywhere but at the end is refused as {cmd:twoway}
    refuses it, {cmd:mcolor(red .. blue):  invalid syntax}, r(198), and an
    element that a y uses is held to the option's bounds as a single value
    is.  An empty quoted element, {cmd:""}, is a {cmd:.}, as in
    {cmd:twoway}.  An element with an {cmd:=} glued inside or after it,
    {cmd:mcolor(red=blue)} or {cmd:mcolor(red=)}, leaves its y at the
    default, silently, as {cmd:twoway} draws it; one led by a glued
    {cmd:=}, {cmd:mcolor(=blue)}, is refused, r(198), as {cmd:twoway}
    refuses it; and one opening with a parenthesis, {cmd:mcolor((red))}
    or {cmd:mcolor("(red)")}, is refused in {cmd:twoway}'s words,
    {cmd:option(s) ( red ) not allowed}, r(198).  A quoted element of blanks, {cmd:" "}, is refused when a
    y uses it: {cmd:scatter mpg turn weight, mcolor(" " blue)} stops with
    {cmd:dash: mcolor() element 1 is blank; use . for the default (got: " " blue)},
    r(198); write {cmd:.} for the default.  {cmd:twoway} also refuses a used
    blank element, with a different message; an element past the last y is
    not checked.  The options read this way are {cmd:mcolor()},
    {cmd:msymbol()}, {cmd:msize()}, {cmd:msangle()}, {cmd:mfcolor()},
    {cmd:mlcolor()}, {cmd:mlwidth()}, {cmd:mlabcolor()}, {cmd:mlabsize()},
    {cmd:mlabposition()}, {cmd:mlabgap()}, {cmd:mlabangle()},
    {cmd:mlabformat()}, {cmd:lcolor()}, {cmd:lwidth()}, {cmd:lpattern()},
    {cmd:clcolor()}, {cmd:clpattern()}, {cmd:clwidth()}, {cmd:color()},
    {cmd:fcolor()}, {cmd:fintensity()}, {cmd:bfcolor()}, {cmd:blcolor()},
    {cmd:acolor()}, {cmd:alcolor()}, {cmd:alwidth()} and {cmd:alpattern()}.
    {cmd:mlabel()}, {cmd:jitter()}, {cmd:base()} and {cmd:barwidth()} are
    read the same way, one element per y:
    {cmd:scatter mpg turn weight, mlabel(make rep78)} labels {cmd:mpg}'s
    markers with {cmd:make} and {cmd:turn}'s with {cmd:rep78}, and
    {cmd:bar y1 y2 x, base(10 20) barwidth(0.4 0.8)} draws each series from
    its own base at its own width.  A lone value applies to the first y, so
    {cmd:mlabel(make)} labels the first y alone.  In {cmd:mlabel()},
    {cmd:.} leaves that y unlabelled, and {cmd:twoway}'s refusals are kept,
    in its words: {cmd:..} or {cmd:...} anywhere
    ({cmd:.. not allowed in option mlabel()}, r(198)), {cmd:=}
    ({cmd:=exp not allowed}, r(101)), a list of {cmd:.} alone
    ({cmd:too few variables specified}, r(102)), and a variable that does
    not exist, even past the last y, r(111).  A list in {cmd:barwidth()} on
    {cmd:rbar}, {cmd:histogram}, {cmd:rcap} or {cmd:rspike}, or in
    {cmd:base()} on {cmd:rbar} or {cmd:histogram}, is refused as
    {cmd:twoway} refuses it ({cmd:option barwidth() not allowed}, r(198)).
    Each {cmd:jitter()} or {cmd:barwidth()} element a y uses is held to 0
    to 100 or to positive, which {cmd:twoway} does not check; elements past
    the last y are not checked.

{phang2}    {cmd:p}{it:#}{cmd:()} for one y of several: style options only, and none on a confidence-interval fit; see {help dash##pnum:p1() to p20()}.

{phang2}    {cmd:contour} with {opt levels()} refuses an option it does not know, which {cmd:twoway} ignores there; see {help dash##contour_unknown:An option contour does not know}.

{phang2}6.  {ul:Variable and value labels used automatically.}
    {cmd:dash} reads variable labels (they title the axes, key the legend,
    name the tooltip rows and the colour key, and title filter widgets)
    and value labels (for filter dropdowns, the titles of
    {cmd:by()} panels, marker labels, the legend of a discrete
    {cmd:colorvar()} and the CSV download) without any additional options.
    An axis is labelled with numbers, as in {cmd:twoway}, unless its
    {cmd:xlabel()}/{cmd:ylabel()}, on either axis,
    gives the sub-option {cmd:valuelabel} (minimum {cmd:val}): then each
    tick at a labelled code shows its label -- through the x variable's
    labels for x options and the first y variable's for y options, on every
    {cmd:by()} panel -- and an explicit {cmd:"}{it:text}{cmd:"} for the
    same tick wins, as in {cmd:twoway}.  A hover tooltip shows the value
    label of a {cmd:hover()} variable, as {cmd:list} and {cmd:browse} do,
    before and after any filter move.  A variable with no label is
    named by its name there, as {cmd:twoway} names it; a label of blanks
    is drawn as given, except on a filter widget, which then shows the
    name.
    A {cmd:histogram} layer is keyed {cmd:Density}, {cmd:Percent},
    {cmd:Frequency} or {cmd:Fraction}, and a {cmd:kdensity} layer
    {cmd:kdensity} {it:varname}, as in {cmd:twoway}.  Every other layer
    is keyed as {cmd:twoway} keys it (see Statistical Layer Options).

{phang2}7.  {ul:Options dash takes that twoway refuses:} {cmd:hover()} and
    {cmd:table}; see {help dash##dashonly:dash's own options}.


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
({cmd:.py} is appended to a {cmd:saving()} name that does not end in it).
See {help dash##dashboard_options:Dashboard Options}.

{dlgtab:dash serve}

{pstd}
Launches a Bokeh Server serving the current registry as a live dashboard.
The server runs in the foreground: Stata waits until you press Break
(Ctrl+C in console Stata), the optional {cmd:timeout()} expires, or Stata
itself exits.  When a filter moves, the
server recomputes, from the rows the filters leave, every layer computed
from the data -- a histogram's bins as well as its bars, a fitted or
smoothed line, a kernel density curve -- and every KPI card that follows
the filters.  A saved dashboard recomputes those cards, its kernel density
curves, its histogram bar heights (and the bins of a histogram on the
default grid), its {cmd:lfit}, {cmd:qfit},
{cmd:fpfit}, {cmd:lowess}, {cmd:lpoly}, {cmd:mband} and {cmd:mspline} lines,
its {cmd:lfitci}, {cmd:qfitci}, {cmd:fpfitci} and {cmd:lpolyci} lines
and bands and, up to 1,000 distinct points, its {cmd:contour} and
{cmd:contourline} layers in the browser, and keeps its other computed
layers, and the bins a histogram's {cmd:bin()}, {cmd:width()},
{cmd:start()} or {cmd:discrete} set, as they were built; both re-scale every
axis, the second axes' ranges included, over the rows kept; see
{help dash##server_mode:Server Mode}.  The dashboard opens only through a
link holding a key made for each launch; see
{help dash##server_mode:Server Mode}.

{pstd}
{ul:Options:}

{synoptset 20 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmd:port(}{it:#}{cmd:)}}TCP port for the Bokeh Server; must be
    an integer in the range 1024 to 65535, written in digits only (no sign,
    decimal point or exponent); default 5006; a port another program holds
    is refused with r(198) and named{p_end}
{synopt:{cmd:nobrowser}}do not open a browser window automatically.  The
    rule is {cmd:dash build}'s: a registered graph's {cmd:nodraw} has the
    same effect, and so does setting the global {cmd:$dash_nobrowser}, which
    keeps every {cmd:dash} window shut for the session; see
    {help dash##nobrowser_global:The global dash_nobrowser}{p_end}
{synopt:{cmd:timeout(}{it:#}{cmd:)}}stop the server after {it:#} minutes,
    at most nine digits; 0 means run until Break (default){p_end}
{synopt:{cmd:maxsessions(}{it:#}{cmd:)}}sessions open at once, an integer
    from 1 to 1,000,000 in digits only (default 20); a page asked for
    beyond it gets HTTP 503; see
    {help dash##limits:Resource limits}{p_end}
{synopt:{cmd:idletimeout(}{it:#}{cmd:)}}close a session after {it:#}
    minutes with no filter, brush or download, 0 to 525600 in digits only;
    0 means never (default 60){p_end}
{synoptline}

{pstd}
{cmd:dash serve} also accepts every dashboard option {cmd:dash build}
accepts -- {cmd:title()}, {cmd:subtitle()}, {cmd:layout()}, {cmd:link()},
{cmd:filter()}, {cmd:theme()}, {cmd:scheme()}, {cmd:tabs()},
{cmd:filterposition()} and {cmd:csv} -- with the same meanings and the same
validation.  {cmd:saving()}, {cmd:replace} and {cmd:server}, which write a
file, are named in a note and ignored: {cmd:dash serve} writes none.
See {help dash##dashboard_options:Dashboard Options}.

{pstd}
{ul:Inheriting a previous build.}  If a {cmd:dash build} has already run in
this session, {cmd:dash serve} reuses its options for anything you do not
restate, so

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash build, saving(dashboard.html) filter(foreign, type(dropdown)) replace}{p_end}
{phang2}{cmd:. dash serve, port(5006)}{p_end}

{pstd}
serves the dashboard you just built, filter and all.  An option given on
{cmd:dash serve} always wins over the inherited one.  {cmd:dash clear}
discards the remembered options along with the registry.

{dlgtab:dash clear}

{pstd}
Empties the registry: every graph and KPI card goes, and so do the options
remembered from the last {cmd:dash build} -- the globals
{cmd:$dash_graph_registry}, {cmd:$dash_json_*}, {cmd:$dash_spec_*},
{cmd:$dash_fpts_*}, {cmd:$dash_kpi_*} and {cmd:$dash_opts_*}.  Settings stay:
{cmd:$dash_nobrowser} and the {cmd:$dash_max_*} limits remain until you drop
them (see {help dash##limits:Resource limits}).  It also removes this
session's preview pages, but one a browser was asked to open in the last
minute (see {help dash##tempfiles:Temporary files and privacy}).  Run this
before starting a new dashboard definition.


{marker dashboard_options}
{title:Dashboard Options}

{pstd}
The following options are available on {cmd:dash build}.

{synoptset 24 tabbed}
{synopthdr}
{synoptline}
{synopt:{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}}required; the file to
    write: {cmd:.html} is appended to a name that does not end in it and a
    {cmd:.gph} suffix is replaced, as on the one-line form, and so is a
    suffix {cmd:graph export} writes ({cmd:.png}, {cmd:.svg}, {cmd:.pdf},
    {cmd:.eps}, {cmd:.ps}, {cmd:.jpg}, {cmd:.jpeg}, {cmd:.tif}, {cmd:.gif},
    {cmd:.emf}, {cmd:.wmf}), with a note;
    {cmd:saving(}{it:filepath}{cmd:, replace)} overwrites and {cmd:asis} is
    accepted; see {help dash##saving_chars:Characters in saving()}{p_end}
{synopt:{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}}dashboard page title{p_end}
{synopt:{cmdab:sub:title}{cmd:(}{it:string}{cmd:)}}dashboard subtitle{p_end}
{synopt:{cmdab:lay:out}{cmd:(}{it:spec}{cmd:)}}grid layout; see
    {help dash##layout:Layout}{p_end}
{synopt:{cmd:link(}{it:names}{cmd:)}}names of graphs to link for brushing,
    one link group a copy; see {help dash##linking:Linking and Brushing}{p_end}
{synopt:{cmdab:br:ush}{cmd:(}{it:mode}{cmd:)}}what a selection does to the
    rows it leaves out: {cmd:highlight} (the default) draws them faint,
    {cmd:filter} hides them; see {help dash##linking:Linking and Brushing}{p_end}
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
    instead of a standalone HTML file; {cmd:.py} is appended to a
    {cmd:saving()} name that does not end in it; does not block or open a browser; see
    {help dash##saving_chars:Characters in saving()}{p_end}
{synopt:{cmdab:nobr:owser}}write the dashboard but do not open it in a
    browser.  Stata's own {cmd:nodraw} on the graph has the same effect, and
    setting the global {cmd:$dash_nobrowser} to any non-empty value suppresses
    the window for a whole session -- for {cmd:dash build}, the one-line
    form and {cmd:dash serve} alike; in batch and after
    {cmd:set graphics off} no window opens anyway; see
    {help dash##nobrowser_global:The global dash_nobrowser}{p_end}
{synopt:{cmd:replace}}overwrite output file if it already exists{p_end}
{synoptline}

{marker saving_chars}
{pstd}
{ul:Characters in saving().}  A {cmd:saving()} path may hold what a file
name on your system may hold, as {cmd:twoway}'s {cmd:saving()} may: a
{cmd:..} segment, and {cmd:;} {cmd:&} {cmd:|} {cmd:<} {cmd:>} among the
rest.  Five things are refused, {cmd:r(198)}: a double quote, a backquote
and a dollar sign, which Stata reads as macro text; a control character,
such as a tab or a line break; and a file name starting with {cmd:-}, which
a command would read as an option.  Other characters, {cmd:%}, {cmd:!}
and {cmd:^} among them, are written as typed, as {cmd:twoway}'s
{cmd:saving()} writes them.  On a Mac and on Unix the page is opened with
its path in single quotes, where nothing in it is special, and the
{cmd:To launch:} line of {cmd:dash build, server} quotes it the same way.
On Windows, dash does not open a page whose
path holds {cmd:%}, {cmd:!}, {cmd:^}, {cmd:&}, {cmd:|}, {cmd:<}, {cmd:>} or
{cmd:;}, because Windows' command shell, through which the page would be
opened, reads them as instructions: the page is written, dash prints its
path, and you open it yourself.  This includes the one-line form's preview
page when the name of your user folder holds such a character.  On
Windows the {cmd:To launch:} line keeps double quotes and says so when the
path holds {cmd:%} or {cmd:!}, which cmd.exe expands in a pasted line.

{marker nobrowser_global}
{pstd}
{ul:The global dash_nobrowser.}  Set to any non-empty value --
{cmd:global dash_nobrowser 1} -- it keeps every {cmd:dash} window shut for
the rest of the session, as {cmd:nobrowser} does for one command:
{cmd:dash build} writes its file and opens nothing; the one-line form with
neither {cmd:saving()} nor {cmd:name()} writes its dashboard to a page in
{cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/previews/} (see
{help dash##tempfiles:Temporary files and privacy}), says where, and opens
nothing; and {cmd:dash serve} starts its server
without opening a browser.  Only whether it holds a value counts, so
{cmd:global dash_nobrowser 0} keeps windows shut too.  {cmd:dash clear}
leaves it set; {cmd:macro drop dash_nobrowser} lets windows open again.
The one-line form has no {cmd:nobrowser} option: written there, it is
refused as {cmd:twoway} refuses it, {cmd:option nobrowser not allowed},
{cmd:r(198)}, and nothing opens; the global, the graph's {cmd:nodraw} or
{cmd:saving()} keeps that window shut.  The global is meant for
interactive sessions and test suites that should open no window.

{pstd}
{ul:Batch and set graphics off.}  As {cmd:twoway} displays no graph in
batch ({cmd:c(mode)} is {cmd:batch}) or after {cmd:set graphics off},
{cmd:dash} opens no window there, whatever is set: {cmd:dash build} and the
one-line form write the page and print where it is, a one-line preview
says it is temporary, and {cmd:dash serve} starts its server without a
browser.  Interactive Stata, the console included, opens the window as
before.


{marker export}
{title:Exporting}

{pstd}
Every dashboard can save its figures as a PNG image, with the save button
on the toolbar (see {help dash##toolbar:The toolbar}).  With {cmd:csv} it
can also give you its data.

{pstd}
{ul:graph export.}  A dashboard is drawn in the browser, not in a Stata
Graph window, so {cmd:graph export} cannot write it: {cmd:graph export}
writes the graph displayed in a Graph window, and with none it stops with
"no Graph window open", {cmd:r(601)}.  If Stata holds an earlier graph,
{cmd:graph export} after {cmd:dash} writes that graph.  So that this is never
silent, a {cmd:dash} command that writes a file -- the one-line form and
{cmd:dash build} -- prints one note when Stata holds a graph in memory (the
graphs {cmd:graph dir, memory} lists), naming up to five of them:
{cmd:(note: dash: graph export writes the graph in Stata's Graph window,}
{cmd:not this dashboard; graphs in memory: Graph)}.
{cmd:dash} never draws, drops or changes a Stata graph.  In batch, a graph
removed with {cmd:graph drop} can still be the one {cmd:graph export} writes;
it is no longer in memory, and no note is printed.

{pstd}
{ul:Images.}  The toolbar's save button writes the figures as a PNG image at
the screen's resolution.  Its Save as SVG button writes the whole
dashboard as a vector SVG file, and its Save dashboard button writes the
whole dashboard as a PNG (see {help dash##toolbar:The toolbar}).  A do-file
cannot write an image of a dashboard:
that needs a web browser driven from Stata, which {cmd:dash} does not ship.
A do-file finds the page in {cmd:r(filename)} (see
{help dash##results:Stored results}).  {cmd:saving()} always writes HTML
({cmd:.py} with {cmd:server}): a name ending in a suffix {cmd:graph export}
writes -- {cmd:.png}, {cmd:.svg}, {cmd:.pdf}, {cmd:.eps}, {cmd:.ps},
{cmd:.jpg}, {cmd:.jpeg}, {cmd:.tif}, {cmd:.gif}, {cmd:.emf} or {cmd:.wmf}, in
any case -- has that suffix replaced, with a note, on the one-line form and
{cmd:dash build}: {cmd:saving(fig.png)} writes {cmd:fig.html}.
({cmd:twoway}'s {cmd:saving(fig.png)} writes a {cmd:.gph} file named
{cmd:fig.png}.)  The figures are drawn on an HTML canvas; {cmd:dash} has no
SVG drawing mode, because a figure drawn as SVG cannot be saved by the
toolbar's button.

{pstd}
{ul:Printing.}  Printing the page from the browser prints it 1000 pixels
wide, without the toolbars and the filters, and gives the screen back its
own layout afterwards; this is so in both modes.  With {cmd:tabs()} it
prints every tab, each on a page of its own and scaled to fit the paper:
the tab's graphs, its open data tables and the tab strip with that tab
marked, drawn as Save dashboard draws them; the tab that is showing stays
the one that shows.

{pstd}
With {cmd:csv}, the dashboard carries a {bf:Download CSV} button beside its
filters (or on its own, when there are none).  It downloads
{it:dashboard.csv}: every observation the filters currently leave, in the
order of the data, with a column for every variable the dashboard uses -- in
the order the dashboard first names them, graph by graph and card by card as
they are registered and then its filters, not in the order of the dataset.
Only the filters count; a selection brushed on a graph and a graph's own
{cmd:if} or {cmd:in} do not.  A filter at its full extent -- a range spanning
every value, a
slider at its minimum -- restricts nothing, as {bf:All} does in a dropdown.
Once moved, a range or slider filter drops observations whose value is
missing, as {cmd:if} {it:x} {cmd:>=} {it:value} does in {cmd:dash}.

{pstd}
The file is written as Stata's {cmd:export delimited} writes one, with these
differences: a date is written in ISO 8601 ({cmd:2020-01-16}; for {cmd:%tc},
{cmd:2020-01-15 13:45:30.25}; for {cmd:%ty}, the year; for {cmd:%tw},
{cmd:%tm}, {cmd:%tq} and {cmd:%th}, the first day of the period); a number is
written as the shortest decimal that reads back as the same number, with a
leading zero ({cmd:0.5} and {cmd:1e-7}, where {cmd:export delimited} writes
{cmd:.5} and {cmd:1.00000000000e-07}), and a {cmd:float} variable's value as
the shortest decimal that reads back as the same float ({cmd:0.1}, not
{cmd:0.10000000149011612}); an extended missing value ({cmd:.a} to
{cmd:.z}) is an empty field, as {cmd:.} is; a text value that begins with
{cmd:=}, {cmd:+}, {cmd:-}, {cmd:@}, a tab or a carriage return is written
after an apostrophe, so that a spreadsheet shows it rather than runs it as a
formula; every line ends in a carriage return and a line feed, as RFC 4180
has it (Stata for Mac ends one in a line feed alone); and the file is UTF-8
with a byte-order mark, which Excel needs and {cmd:import delimited} reads
through.  A value-labelled variable is written as its labels, as
{cmd:export delimited} writes it by default.

{pstd}
{cmd:csv} is off unless asked for, because it lets anyone who opens the
dashboard download every row of every variable it uses -- including one that
only a KPI card summarises.  Without {cmd:csv} a saved dashboard holds only
the observations its graphs, cards and filters select (see
{help dash##description:Description}); with it the page holds them all, so
that the download can be written in the browser, but a served one sends the
browser only what it draws.  When served, each click is computed on the server from the
same filters, and a session may download twice at once and then once every
five seconds.  {cmd:dash serve} inherits {cmd:csv} from the preceding
{cmd:dash build}, as it inherits every dashboard option.


{marker accessibility}{...}
{title:Accessibility}

{pstd}
Saved and served dashboards name their parts for screen readers.  Each
graph is a named group -- an image only when it has no toolbar -- named by
its {cmd:title()} text, or, without one, by its first plot, as in "scatter of mpg versus weight, 1 more layer" (variable
names, not labels; at most 120 characters).  Each filter, the
{bf:Reset filters} button and the {bf:Data table} button is named by its
title, each slider handle by its filter's title, each data table by its
graph's name and each KPI card by its title (else its name).  The served
"Updating..." line and the saved page's error line are status messages.

{pstd}
The tabs of {cmd:tabs()} work from the keyboard: Tab moves to the active
tab, the left and right arrows move to the previous and next tab (wrapping),
Home and End to the first and last, and Enter or Space opens the focused
tab.

{pstd}
Every scheme dash ships meets the WCAG AA contrast of 4.5:1 for its text on
the graph region, the plot region, the legend and KPI boxes, and for its
tick labels on the plot region; the lowest is {cmd:economist}'s KPI value on
its box, 13.8:1.  Colours you give in options are not checked.  The pages are
checked in dash's tests with axe-core, an automated accessibility checker,
for WCAG 2.1 A and AA; an automated check does not find every barrier.  The
interface text is English only.


{marker results}{...}
{title:Stored results}

{pstd}
{cmd:dash} stores the following in {cmd:r()}:

{p2colset 5 20 24 2}{...}
{p2col 5 20 24 2: Macros}{p_end}
{p2col:{cmd:r(filename)}}the file the command wrote, as an absolute path{p_end}
{p2colreset}{...}

{pstd}
{cmd:r(filename)} is stored by the commands that write a file: the one-line
form with {cmd:saving()} (the page), the one-line form without it (the
preview page in {cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/previews/}),
{cmd:dash build} (the page), and {cmd:dash build} with {cmd:server} (the
{cmd:.py} app).
It is the path the "saved to" line shows, joined to the working directory
when it is relative, so it still names the file after a {cmd:cd}.  A preview
is temporary: the newest five of a session are kept, and {cmd:dash clear}
removes the session's previews (see {help dash##tempfiles:Temporary files and privacy});
use {cmd:saving()} to keep a page.  Registering a graph or a KPI card,
{cmd:dash clear} and {cmd:dash serve} store nothing; {cmd:dash serve} writes
no file of yours, and the key in its address is never stored.  A command
that stops with an error stores nothing.  As after {cmd:twoway}, every
{cmd:dash} command replaces the {cmd:r()} results of the command before it.


{marker layout}
{title:Layout}

{pstd}
The {cmd:layout()} option controls how graphs and KPI cards are arranged
in the dashboard grid.

{phang2}{cmd:layout(auto)} -- {cmd:dash} chooses a square-ish grid from
    the number of registered items: {it:n} items take ceil(sqrt({it:n}))
    columns, so four make a 2 x 2 grid and five a 2 x 3 one.  The figures'
    proportions count too: when any figure is at least three times as wide
    as it is tall, every item takes a row of its own, and when one is at
    least 1.8 times as wide, the grid has one column fewer.  This is the
    default.  Items fill the grid in the order they were registered,
    graphs and KPI cards alike, in both render modes.

{phang2}{cmd:layout(}{it:rows} {it:cols}{cmd:)} -- explicit grid dimensions.
    Example: {cmd:layout(2 3)} asks for a grid with 2 rows and 3 columns.
    Items fill it row by row, left to right.  A cell no item reaches is
    left empty, and a row or column after the last item is not drawn:
    two items in {cmd:layout(2 3)} sit side by side, each half the width.
    With more items than cells, rows are added below.  A grid may have at
    most as many cells as a dashboard may hold graphs and KPI cards
    ({cmd:$dash_max_graphs}, default 100; see {help dash##limits:Limits});
    a larger one is refused with {cmd:r(198)}, because {cmd:dash} builds
    every cell of the grid, empty or not, before drawing it.

{phang2}{cmd:layout(}{it:name}{cmd::}{it:row}{cmd:,}{it:col} ...{cmd:)} --
    explicit placement.  Each named item is placed at the specified
    {it:row},{it:col} position (1-indexed; a placement that uses 0
    anywhere is read 0-indexed).  Example:
    {cmd:layout(s1:1,1 s2:1,2 k1:2,1)}.  A registered item the placement
    does not name takes the first free cell, in registration order, and
    rows are added when none is free.  The largest row times the largest
    column is held to the same limit as a {it:rows} {it:cols} grid.  Every
    name must be a registered graph or KPI card, as in {cmd:link()}.

{phang2}{cmd:layout(bs}[{cmd::} {it:name}{cmd:=}{it:span} ...]{cmd:)} --
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
    spans on a grid that narrows with the window, keeping its spans, and
    below 768 pixels of window stacks every item into one column.

{pstd}
{ul:At phone width.}  No dashboard scrolls sideways.  Every grid -- a
{cmd:layout(}{it:rows} {it:cols}{cmd:)}, placement or automatic grid, each
tab's grid, and each {cmd:by()} graph's grid of panels, linked or not --
gives its columns equal shares of its width, and a grid of {it:n} columns
narrower than {it:n} x 240 pixels stacks its cells into one column, each
the full width of the grid, row by row in reading order.  So on a phone
every figure and card takes the whole width, as under {cmd:layout(bs)}; a
1 x 4 grid at 768 pixels is one column of four; and two facet panels in a
cell 351 pixels wide sit one above the other.  The test is the grid's own
width, not the window's, so a facet grid in a narrow cell or tab stacks
while the grid around it keeps its columns.  The filter bar wraps onto
further lines, and below 768 pixels {cmd:filterposition(left)}'s sidebar
moves above the dashboard.  A KPI card narrows below its usual 160 pixels
when its cell is narrower.  The served app does the same, on a phone as
in a narrow window: both pages declare a viewport.

{pstd}
A {cmd:layout()} that is not one of these forms as a whole, that names an
item the registry does not hold, that places an item more than once, or that
gives a span outside 1 to 12 is refused with {cmd:r(198)}; nothing is drawn
some other way in silence.  Two names placed in the same cell are refused,
and the message names both.


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

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash kpi mean(mpg), title("Avg MPG") name(k1)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash scatter mpg length, name(s2)}{p_end}
{phang2}{cmd:. dash histogram mpg, name(s3)}{p_end}
{phang2}{cmd:. dash build, saving(d.html) tabs(Overview: k1 s1 / Detail: s2 s3) replace}{p_end}
{phang2}{cmd:. dash build, saving(d.html) tabs(Overview: k1 s1, layout(1 2) / Detail: s2 s3) replace}{p_end}

{pstd}
A tab may end with {cmd:, layout()} in the grid form ({cmd:layout(1 2)},
as in the second build above) or the placement form
({cmd:layout(g1:1,1 g2:1,2)}) over that tab's names, each name and each
cell used once; a tab without one is drawn in its automatic grid.  The
first comma after a tab's colon ends its names.

{pstd}
Tab titles are used exactly as written, less the blanks around them; the
first colon ends a title, so a title cannot hold a colon, nor a {cmd:/}.  A
group written without a colon is titled by its place: {cmd:Tab 2} for the
second.  A registered item named in no tab is still drawn, below the tabs.
A name that is not in the registry is refused, as {cmd:layout()} refuses
one, and the message names it; so is a tab's {cmd:layout()} that is not one
of its two forms over the tab's names.  {cmd:tabs()} works with every
{cmd:layout()}.  At most 50 tabs are drawn, the first 50: a note gives the
number asked for and the global that raises the limit (see
{help dash##limits:Resource limits}), and an item that only the undrawn
tabs name is drawn below the tabs.


{marker linking}
{title:Linking and Brushing}

{pstd}
Graphs in the same link group draw their observations from a single Bokeh
{cmd:ColumnDataSource}.  That source holds the observations the group's
graphs draw -- each graph's and each layer's {it:if} and {it:in} together
-- and no other.  Selecting observations in one graph (via
box-select or lasso-select) selects them in that source, and every linked
graph highlights them where it draws them as markers: in its
{cmd:scatter}, {cmd:connected} and {cmd:dot} layers, and on {cmd:rspike}
and the markers of {cmd:rconnected}, which draw the group's rows in both
modes.  Observations that are not selected keep their markers' size,
symbol, colours and outline and are drawn faint,
never more opaque than they are drawn unselected.  The other layers -- lines (the line of {cmd:connected} and of
{cmd:rconnected} too), areas, bars, droplines, fits and their bands,
smoothers, densities, histograms, and the other range and paired-coordinate
plots -- are drawn from data of their own and do not show a selection.  An
{cmd:rbar} shows it in neither mode: its bars are drawn from its own rows.
A box or lasso selection on a {cmd:histogram}'s bars, or on what
{cmd:recast()} draws for them, selects the observations those bars count, as if they had been selected one by one:
the group's other graphs and the KPI cards follow them.  On the saved page
this holds until a filter moves; after a move the bars select nothing.

{pstd}
{cmd:link(}{it:name1} {it:name2} [{it:name3} ...]{cmd:)} -- link the
specified graphs.  All graphs must have been registered with {cmd:name()};
a name the registry does not hold is refused with {cmd:r(198)}, and a KPI
card's name is accepted and has no effect.  {cmd:link()} may be given
more than once: each copy is a link group with a source of its own, so
{cmd:link(g1 g2) link(g3 g4)} brushes g1 with g2 and g3 with g4, and a
selection in one group does not reach the other.  A graph named in two
groups is refused with {cmd:r(198)}.

{pstd}
{cmd:link(_all)} -- link all registered graphs.  {cmd:_all} stands alone:
beside other names, or beside another {cmd:link()}, it is refused with
{cmd:r(198)}, and no graph may be named {cmd:_all}.

{pstd}
{cmd:brush(filter)} -- a selection hides the observations it leaves out
instead of drawing them faint: in the brushed graph, which then shows the
selection only, in the other graphs of its link group, and in a linked
graph's data table, which lists the selected rows; clearing the selection
shows every row again.  Every KPI card follows the selection, whatever its
{cmd:update()}.  {cmd:brush(highlight)}, the default, is the faint drawing
described above.  Any other word is refused with {cmd:r(198)}.

{pstd}
Selections in several graphs act together, in both modes: a KPI card that
follows a brush counts the observations every current selection holds, and
clearing one selection leaves the others' effect.

{pstd}
Each graph of a group keeps its own {it:if} and {it:in}, applied before the
link: the group's source holds the rows any of its graphs draws, and each
graph draws only its own.  Below, {cmd:g2} draws the 22 foreign cars and
{cmd:g1} all 74; a selection of domestic cars in {cmd:g1} highlights
nothing in {cmd:g2}, and a selection in {cmd:g2} highlights those foreign
cars in {cmd:g1}:

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(g1)}{p_end}
{phang2}{cmd:. dash scatter mpg price if foreign == 1, name(g2)}{p_end}
{phang2}{cmd:. dash build, saving(linked.html) link(g1 g2) replace}{p_end}

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
{synopt:Undo}step back through your pans, zooms and box and lasso
    selections.{p_end}
{synopt:Redo}step forward again.{p_end}
{synopt:Reset}return to the extent the last filter move gave the axes, and clear the
    selection and what Undo would step back through.{p_end}
{synopt:Save}write the figures to a PNG image; see below.{p_end}
{synopt:Save as SVG}write the whole dashboard as a vector SVG file; on a
    {cmd:by()} graph's own panels, those panels alone; see below.{p_end}
{synopt:Save dashboard}write the whole dashboard as a PNG image; see
    below.{p_end}
{synoptline}

{pstd}
Every figure has tooltips, and a hover button that turns them off and
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
{cmd:g1}.  The save button's image holds only the figures: a KPI card in
a grid is left blank, and the title, the filters and the tab strip, which
sit outside every grid, are not in it.

{pstd}
{ul:Saving the whole dashboard.}  Save dashboard (a PNG) and Save as SVG (a
vector image) write the whole dashboard, top to bottom: the title and
subtitle, each filter's title and its current value, the tab strip with the
tab that is showing in bold and underlined, the KPI cards with their titles,
values, subtitles and colours, and then the image of the grid whose toolbar
you used.  The text is what the page shows at that moment, after any filter
you moved.  The files are {cmd:dashboard-full.png} and
{cmd:dashboard-full.svg}, or {cmd:g1-full.png} and {cmd:g1-full.svg} for an
item {cmd:layout(bs)} places on its own; there each item's file holds the
header, the filters and the tab strip above that item alone, and a KPI card,
an item of its own, has no button.  On the panels of a {cmd:by()} graph in a
grid, Save as SVG writes those panels alone, {cmd:dashboard.svg}.  A figure
with more than 10,000 points makes a large SVG.  An open data table is drawn
where it sits: its column titles and as many of its rows as it shows, in the
order of the rows it lists (a sort you clicked is not kept); a folded table
is not drawn.  The
text is drawn in the browser's sans-serif font, which can differ from the
page's.  Your browser decides where the file goes.


{marker table}
{title:Data tables}

{pstd}
{cmd:table} is a graph option of {cmd:dash}'s own ({cmd:twoway} draws no
table; see {help dash##dashonly:dash's own options}).  It puts a {bf:Data table} button under the graph, or under the
panels of a {cmd:by()} graph, and behind it a table of the observations
the graph draws.  The table is folded away when the page opens, so the
layout is the graph's alone until you press the button.

{synoptset 24 tabbed}{...}
{synopthdr:option}
{synoptline}
{synopt:{opt table}}a folded data table under the graph.{p_end}
{synopt:{opt table(rows(#) open)}}the same, listing at most {it:#}
    observations (a whole number from 1 to 100,000; the default is
    {cmd:$dash_max_table_rows}, 1,000), unfolded when the page opens with
    {cmd:open}.  Write {cmd:table} or {cmd:table()}, not both; a graph takes
    one, and any other word in the parentheses is refused with
    {cmd:r(198)}.{p_end}
{synoptline}

{pstd}
The columns are the variables the graph plots, in the order its tooltip
names them, then its {cmd:hover()} variables; a {cmd:by()} graph's own
variables come first, each row in its panel.  A column is headed by the
variable's label, else its name, and every cell is the value as Stata
displays it: the variable's display format, its value label when it has
one, a date in its date format, and {cmd:.} for a missing value.  Click a
heading to sort by it; the table scrolls through its rows.  It lists the
rows the graph draws, after its {cmd:if} and {cmd:in}, and follows every
filter move, in a saved page and under {cmd:dash serve} alike.  When the
graph draws more rows than the table lists, the first are listed, with
the note {it:The table lists at most # rows of those drawn.}  The CSV
download is unchanged: it writes the data, not the table.


{marker filters}
{title:Filters}

{pstd}
Each {cmd:filter()} option on {cmd:dash build} or {cmd:dash serve} adds a
widget above the dashboard -- beside it, with {cmd:filterposition(left)} --
that filters observations across all graphs and KPI cards (unless
excluded; a KPI card follows filters as its {cmd:update()} says).

{pstd}
Syntax:
{cmd:filter(}{it:varname}[{cmd:,}
{cmd:type(}{it:filter_type}{cmd:)}
{cmd:exclude(}{it:namelist}{cmd:)}
{cmd:label(}{it:string}{cmd:)}
{cmd:direction(}{cmd:ltr}|{cmd:rtl}{cmd:)}]{cmd:)}

{pstd}
{it:varname} may be abbreviated, as anywhere in Stata, and may hold
Unicode letters, as any Stata name may.  Without {cmd:type()} the widget
is a dropdown.  A {cmd:by()} panel left with no rows by a filter is
hidden, its cell left blank, and shown again when rows return.

{phang2}{cmd:type(dropdown)} -- select widget listing every distinct value
    of {it:varname}: a numeric or date variable's values as numbers, a
    string variable's exact text.  When {it:varname} has a missing value
    (a numeric {cmd:.}, or a string's empty string) one more entry,
    {cmd:(missing)}, is listed last; it keeps exactly the observations
    whose value is missing.  Selecting a value keeps the observations equal
    to it -- a number compared as a number, a text compared exactly, so
    {cmd:"01"} and {cmd:"1"} are two values -- in the saved page and the
    served app alike.  A listed value is written in the variable's display
    format, or its value label; values that share one display text are one
    entry that selects them all.
    An "All" option removes the filter.  A dropdown lists at most 1,000
    values: over that, a numeric or date variable is drawn as
    {cmd:type(range)} instead, and a string variable lists its first 1,000
    values in sort order, each with a note (see
    {help dash##limits:Resource limits}).

{phang2}{cmd:type(multi)} -- multi-select widget listing the same values
    as {cmd:type(dropdown)}, {cmd:(missing)} included.  With nothing chosen
    (the box shows {cmd:All}) every observation is kept; with values chosen,
    the observations equal to any of them.  It lists at most 1,000 values
    as a dropdown does: over that, a numeric or date variable is drawn as
    {cmd:type(range)}, and a string variable lists its first 1,000 values
    in sort order, with a note naming the variable and how many values it
    has.

{phang2}{cmd:type(slider)} -- slider that keeps observations where
    {it:varname} is at or above the slider's value; its title ends in a
    greater-than-or-equal sign.

{phang2}{cmd:type(range)} -- range slider that keeps observations where
    {it:varname} is between the low and high slider values, both included.
    A %tw, %tm, %tq, %th or %ty variable's range slider moves over Stata's
    period numbers in steps of one.

{pmore2}
    A slider at its minimum, like a range at its full extent, restricts
    nothing; once moved, either drops the observations whose value is
    missing (see {help dash##export:Exporting}).

{pmore2}
    A widget lists the values of, or spans the range of, the observations
    that the graphs, link group and cards it filters select, after
    {cmd:exclude()}; an observation every {it:if} or {it:in} excludes adds
    no option or bound, and the 1,000-value limit of a dropdown counts those
    observations only.  A filter that reaches no observation -- every graph
    and card excluded, or graphs that draw no observation -- draws a range
    or slider greyed out, and a dropdown that lists only All.

{phang2}{cmd:exclude(}{it:namelist}{cmd:)} -- prevent the filter from
    affecting the specified graphs and KPI cards, each a registered name,
    whatever moves.  Each graph, card, and link group is redrawn on every
    move from the observations kept by the filters that do not exclude it,
    so its state depends only on the widgets' current values.  Excluding a
    {cmd:by()} graph excludes every one of its panels.  A graph in a
    {cmd:link()} group draws from the group's one source, so the group is
    filtered by a filter unless every graph of the group is excluded from
    it.

{phang2}{cmd:direction(}{cmd:ltr}|{cmd:rtl}{cmd:)} -- the direction a
    {cmd:type(slider)} or {cmd:type(range)} widget runs: {cmd:ltr}, the
    default, puts its minimum on the left, {cmd:rtl} on the right.  The
    bounds and the observations kept are the same either way.  Any other
    word, and {cmd:direction()} on a dropdown or multi, stop {cmd:dash build}
    and {cmd:dash serve} with {cmd:r(198)}.

{phang2}{cmd:label(}{it:string}{cmd:)} -- the text shown beside the widget.
    Without it the variable's own label is used, and failing that its name.
    The text may hold any character -- a semicolon, a {cmd:|} or a
    {cmd:||} included.  Put it in double quotes, or in compound double
    quotes when it holds a double quote, if it holds a parenthesis that is
    not balanced; the quotes are not shown.

{pstd}
{cmd:type()} must be one of the four above; any other value is named in a
warning and no widget is built.  Any other sub-option is accepted, named in
a warning, and ignored.  {cmd:dash build} and {cmd:dash serve} stop with
{cmd:r(198)} at a group whose variable is not a valid variable name or
whose {cmd:exclude()} names an item the registry does not hold, and with
{cmd:r(111)} at one whose variable is not in the data.

{pstd}
{ul:More than one filter.}  Give {cmd:filter()} as many times as you need, up
to 20, on the same {cmd:dash build} or {cmd:dash serve} call; past 20 the
first 20 are built and a note names the global that raises the limit (see
{help dash##limits:Resource limits}).  Stata's {cmd:syntax} refuses an
option given twice ({cmd:option filter() not allowed}, {cmd:r(198)}), so
{cmd:dash} collects the {cmd:filter()} options itself before parsing and
joins them with {cmd:||} internally; you never write the {cmd:||}.  Each
group is validated on its own, so {cmd:exclude()} on the second filter is
honoured exactly as on the first.

{pstd}
{ul:Reset filters.}  A dashboard with at least one filter widget ends its
filter row with a {cmd:Reset filters} button, which puts every widget back
to the value it opened with and redraws the dashboard from the opening
observations, in the saved page and the served app alike.

{pstd}
{ul:The dropdown's "All" entry.}  A {cmd:type(dropdown)} widget carries an
{cmd:All} entry that removes the filter.  It is the selected entry when the
dashboard opens, and it is carried in the page as the value {cmd:__all__}
-- or, when the variable's own data holds that string, as {cmd:__all__}
with underscores added until it matches no value -- so a category
{cmd:__all__} is filtered on as normal.

{pstd}
Example:

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash kpi mean(price), title("Avg price") name(k1)}{p_end}
{phang2}{cmd:. dash build, saving(out.html) replace ///}{p_end}
{phang2}{cmd:.     filter(foreign, type(dropdown)) ///}{p_end}
{phang2}{cmd:.     filter(weight, type(range) exclude(k1))}{p_end}


{marker kpi}
{title:KPI Cards}

{pstd}
KPI cards display a single computed statistic as a styled card widget
in the dashboard layout.  They update automatically when filters or
brush selections change (depending on the {cmd:update()} option).

{pstd}
{ul:Syntax:}
{cmd:dash kpi} {it:stat}{cmd:(}{it:varname}{cmd:)} {ifin} {weight} {cmd:,}
{cmdab:ti:tle}{cmd:(}{it:string}{cmd:)}
{cmdab:nam:e}{cmd:(}{it:id}{cmd:)}
[{it:options}]

{pstd}
{it:varname} may hold Unicode letters, as any Stata name may.

{pstd}
{ul:Supported statistics:}

{synoptset 15 tabbed}
{synopthdr:statistic}
{synoptline}
{synopt:{cmd:mean}}arithmetic mean{p_end}
{synopt:{cmd:sum}}sum{p_end}
{synopt:{cmd:count}}number of non-missing observations{p_end}
{synopt:{cmd:dcount}}number of distinct non-missing values{p_end}
{synopt:{cmd:min}}minimum value{p_end}
{synopt:{cmd:max}}maximum value{p_end}
{synopt:{cmd:median}}median (50th percentile){p_end}
{synopt:{cmd:sd}}standard deviation (N-1){p_end}
{synopt:{cmd:var}}variance (N-1){p_end}
{synopt:{cmd:cv}}coefficient of variation, {cmd:sd}/{cmd:mean}{p_end}
{synopt:{cmd:iqr}}interquartile range, {cmd:p75} - {cmd:p25}{p_end}
{synopt:{cmd:skewness}}skewness{p_end}
{synopt:{cmd:kurtosis}}kurtosis, Stata's m4/m2^2{p_end}
{synopt:{cmd:semean}}standard error of the mean, {cmd:sd}/sqrt(N){p_end}
{synopt:{cmd:range}}range, {cmd:max} - {cmd:min}{p_end}
{synopt:{cmd:p25}}25th percentile{p_end}
{synopt:{cmd:p50}}50th percentile (same as {cmd:median}){p_end}
{synopt:{cmd:p75}}75th percentile{p_end}
{synoptline}

{pstd}
Any percentile may be requested as {cmd:p}{it:#}, not only the three listed
above: {cmd:p10}, {cmd:p90} and {cmd:p97.5} are all accepted.  {it:#} is a
number written in decimal, greater than 0 and less than 100 -- the range
Stata's {cmd:_pctile} accepts -- with at most 15 digits, and dash keeps one
spelling of it: {cmd:p097.50} is stored as {cmd:p97.5}, {cmd:p.5} as
{cmd:p0.5}.  Percentiles follow Stata's own rule rather than the
interpolated one most software uses, so {cmd:dash kpi p25(price)} reports
the number {cmd:summarize, detail} reports and {cmd:dash kpi p97.5(price)}
the number {cmd:_pctile price, p(97.5)} reports.  Variance and standard
deviation divide by N-1, and skewness is Stata's biased m3/m2^1.5 -- again,
the values {cmd:summarize, detail} gives.  A card shows these values when
the dashboard opens and after every filter move or brush, in the saved page
and the served app alike.

{pstd}
{cmd:aweight}s, {cmd:fweight}s and {cmd:iweight}s are allowed, as
{cmd:summarize} allows them; see {help weight}.  The weight is a numeric
variable, not an expression: {cmd:[aw=weight/2]} is refused with
{cmd:r(198)}.  Every statistic is then the one {cmd:summarize} with that
weight reports -- {cmd:dash kpi mean(mpg) [aw=weight]} shows the mean
{cmd:summarize mpg [aw=weight]} reports, {cmd:count} is its {cmd:r(N)}
(the sum of the weights for an {cmd:fweight}), {cmd:sum} its {cmd:r(sum)},
percentiles, {cmd:skewness} and {cmd:kurtosis} those of
{cmd:summarize, detail}, and {cmd:semean} is {cmd:tabstat}'s
{cmd:se(mean)}, {cmd:sd}/sqrt({cmd:r(N)}); {cmd:dcount} takes no weight,
but an observation with a missing or zero weight is left out of every
statistic, as {cmd:summarize} leaves it out.  The card stays weighted after
every filter move and brush, in both modes.  {cmd:pweight}s are refused with
{cmd:summarize}'s {cmd:r(101)}, and so is an {cmd:iweight} with
{cmd:median}, {cmd:iqr}, a percentile, {cmd:skewness}, {cmd:kurtosis} or
{cmd:semean}, which {cmd:summarize, detail} and {cmd:tabstat} do not take
one for.

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash kpi mean(mpg) [aw=weight], title("Weighted MPG") name(kw)}{p_end}

{pstd}
{cmd:count} and {cmd:dcount} also take a string variable, and count its
values that are not empty; every other statistic needs a numeric variable
and refuses a string one with {cmd:r(109)}.  Over no observations -- a
filter can leave a card none -- {cmd:count}, {cmd:dcount} and {cmd:sum} are
0 and every other statistic is missing, shown as {cmd:.}, as
{cmd:summarize} has them; {cmd:sd}, {cmd:var}, {cmd:cv}, {cmd:semean},
{cmd:skewness} and {cmd:kurtosis} of one observation are missing too.  Of a date variable, {cmd:mean},
{cmd:min}, {cmd:max}, {cmd:median} and every percentile are dates, and
both the saved page and the served app (see
{help dash##server_mode:Server Mode}) show them as dates: in {cmd:fmt()}'s
format if given, else in the variable's own {cmd:%t} picture, as
{cmd:display} writes them ({cmd:%td} gives {cmd:02jan2001}).  A count, a
distinct count, a spread, a sum or the skewness of a date variable is a
number, shown in {cmd:%9.0g} unless {cmd:fmt()} says otherwise.
Each statistic is taken of the variable's Stata values, as
{cmd:summarize} takes it: {cmd:sd()} of a {cmd:%td} variable is in days
(105.3335 for {cmd:date} in {cmd:sysuse sp500}), {cmd:var()} in days
squared, {cmd:iqr()} in days, {cmd:cv()} is the sd over the mean day
number, and {cmd:sum()} adds up the day numbers, which a note says has no
meaning; the mean of 2001m1 and 2001m3 is 2001m2.

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
    format such as {cmd:%9.2f} or {cmd:%12.0fc} -- {cmd:%}{it:w.d}{cmd:f},
    {cmd:%}{it:w.d}{cmd:g} or {cmd:%}{it:w.d}{cmd:e}, each with {cmd:c}
    and the comma decimal, or any {cmd:%t} picture; anything else,
    including a string format such as {cmd:%12s}, is refused with an
    error; the hexadecimal {cmd:%21x} and the IEEE {cmd:%16H} and
    {cmd:%16L} formats, which {cmd:confirm numeric format} accepts, are
    refused with r(198) too: the page cannot write a hexadecimal or IEEE
    byte dump.  The card shows the text {cmd:display} gives for its format,
    as the page opens, after every filter move and after a brush, saved
    and served: {cmd:fmt()} if given, else the variable's own display
    format ({cmd:%8.0gc} shows {cmd:6,165.3} for auto's mean price),
    else {cmd:%9.0g}; a missing statistic reads {cmd:.}{p_end}
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

{phang2}{cmd:update(filter)} -- KPI recalculates when filter widgets
    change.  This is the default.

{phang2}{cmd:update(brush)} -- KPI recalculates when observations are
    selected via box-select or lasso-select brushing, whichever graph is
    brushed.

{phang2}{cmd:update(both)} -- KPI recalculates on either filter changes
    or brush selections.

{pstd}
A KPI is one card, in {cmd:dash build} and {cmd:dash serve} alike:
{cmd:update()} says how the card follows the dashboard, never which graph
it follows, and a {cmd:by()} graph does not split a card into one per
panel.  For a statistic of each group, register a card per group:

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash kpi mean(mpg) if foreign == 0, title("Domestic") name(kdom)}{p_end}


{marker frames}
{title:Graphs from several frames}

{pstd}
A registered graph is drawn from the frame it was registered in, as
{cmd:twoway} draws from the frame its command runs in.  {cmd:dash} takes
Stata's own prefix and adds no option:
{cmd:frame cars: dash scatter mpg weight, name(g1)} is
{cmd:frame cars: twoway scatter mpg weight}, registered.  So one
{cmd:dash build} can hold graphs of several datasets, each in its own frame,
and the frame {cmd:dash build} runs in, and its data, are left as they were.

{phang2}{cmd:. frame create cars}{p_end}
{phang2}{cmd:. frame cars: sysuse auto, clear}{p_end}
{phang2}{cmd:. frame create sp}{p_end}
{phang2}{cmd:. frame sp: sysuse sp500, clear}{p_end}
{phang2}{cmd:. frame cars: dash scatter mpg weight if foreign, name(g1)}{p_end}
{phang2}{cmd:. frame sp: dash line close date in 1/100, name(g2)}{p_end}
{phang2}{cmd:. dash build, saving(two.html) replace}{p_end}

{pstd}
Each graph is drawn from its own frame's rows: its {it:if} and {it:in},
time-series operators ({cmd:L.close} under that frame's {cmd:tsset}),
{cmd:sort()} and weight expressions ({cmd:[aw=pop/1000]}) are evaluated in
that frame, as {cmd:twoway} evaluates them there.  A variable that graphs of
two frames both use, held in each with another storage kind,
display format, value label or variable label, is drawn in each graph with its own
frame's: {cmd:date} formatted {cmd:%td} in one frame and {cmd:%tm} in
another draws days in the first frame's graphs and months in the second's.
KPI cards read the frame current at {cmd:dash build}.

{pstd}
A {cmd:filter()} applies to every graph whose frame holds its variable, by
that graph's own frame's values; a graph whose frame does not hold it is
added to the filter's {cmd:exclude()} list.  The filter's choices are every
such frame's values, labelled with the first such frame's value labels.

{pstd}
Three shapes are refused at {cmd:dash build}, before anything is written: a
graph whose frame no longer exists ({cmd:frame} {it:name} {cmd:not found},
{cmd:r(111)}, naming the graph); a {cmd:link()} group joining graphs of two
frames ({cmd:r(198)}: a link group draws from one frame, and brushing
follows the link groups); and a {cmd:filter()} whose variable one frame
stores as a string and another as a number ({cmd:r(109)}, naming the
variable and the two frames: one filter control cannot offer both texts and
numbers).  A variable that only one frame's graphs use is never compared.

{marker image}
{title:Image panels}

{pstd}
{cmd:dash image} {cmd:using} {it:filename}{cmd:,} {cmd:name(}{it:name}{cmd:)}
registers a picture, an SVG file, that {cmd:layout()} and {cmd:tabs()}
place by its name as they place a graph or a KPI card, in a saved page and
a served app alike.  {cmd:caption()} is shown beneath the picture and
{cmd:alt()}, which defaults to the caption, else the name, is its text for
a screen reader; both are shown as typed, never as markup.  {cmd:name()}
follows the rules of a KPI card's: a letter or underscore first, then
letters, digits and underscores, at most 18 characters, and
{cmd:name(}{it:name}{cmd:, replace)} to reuse a name.  {cmd:dash clear}
removes image panels with the rest of the registry.

{pstd}
The file is checked when it is registered and read again by
{cmd:dash build} and {cmd:dash serve}.  It must be well-formed SVG with no
{cmd:script} or {cmd:foreignObject} element, no event-handler attribute
({cmd:onload} and the like), no DOCTYPE or entity declaration and no
external reference: a link or {cmd:url()} may only point inside the file
or hold an embedded PNG, JPEG, GIF or SVG image.  A file that breaks one of
these rules is refused with {cmd:r(198)}, and a missing file with
{cmd:r(601)}.  No file is refused for its size; only the number of image
panels is bounded, by {cmd:$dash_max_images} (see
{help dash##limits:Resource limits}).

{pstd}
The page draws the picture inside an image element, which runs no script
and loads nothing from outside the page.  {cmd:link(}{it:page}{cmd:.html)}
makes the picture a link to another page in the same folder: the text must
be a file name made of letters, digits, {cmd:_} or {cmd:-}, then
{cmd:.html} -- no folder, no {cmd:..} and no address -- and anything else
is refused with {cmd:r(198)}.  A saved page and a served app carry the same
relative link; beside a saved page it opens the page in the same folder,
while in a served app it resolves against the app's own address.


{marker server_mode}
{title:Server Mode}

{pstd}
{cmd:dash serve} runs the dashboard as a Bokeh Server application: it writes
the application into a private temporary folder (see
{help dash##tempfiles:Temporary files and privacy}), runs it with Python and
waits until the server stops.  {cmd:dash build, server} writes the same
application to the file {cmd:saving()} names and returns without starting
it.  A {cmd:by()} panel left with no rows by a filter is hidden, its cell left
blank, and shown again when rows return, as on the saved page.  The saved page and the
served app differ as follows:

{col 5}{it:Feature}{col 38}{it:Saved page}{col 59}{it:Served app}
{col 5}{hline 72}
{col 5}Requires internet / server{col 38}No{col 59}Yes (local)
{col 5}Shared as{col 38}one .html file{col 59}one .py, for Python
{col 5}Filter widgets{col 38}JavaScript{col 59}Python callbacks
{col 5}Multi-select, reset{col 38}Yes{col 59}Yes
{col 5}KPI recomputation on filter{col 38}Yes{col 59}Yes
{col 5}Brush/lasso KPI update{col 38}Yes{col 59}Yes
{col 5}Several link groups{col 38}Yes{col 59}Yes
{col 5}brush(filter){col 38}Yes{col 59}Yes
{col 5}Brush on histogram bars{col 38}until a move{col 59}Yes
{col 5}Histogram recompute on filter{col 38}heights and bins{col 59}heights and bins
{col 5}Kernel density on filter{col 38}grid recomputed{col 59}grid recomputed
{col 5}Fit-line recompute on filter{col 38}Yes{col 59}Yes
{col 5}A slider recomputes{col 38}when released{col 59}when released
{col 5}Dates{col 38}Yes{col 59}Yes
{col 5}Toolbar, save as PNG{col 38}Yes{col 59}Yes
{col 5}Toolbar, save as SVG{col 38}Yes{col 59}Yes
{col 5}Toolbar, whole dashboard{col 38}Yes{col 59}Yes
{col 5}Print at a fixed width{col 38}Yes{col 59}Yes
{col 5}{help dash##table:Data table} ({cmd:table}){col 38}Yes{col 59}Yes
{col 5}{cmd:scheme()}, {cmd:theme()}{col 38}Yes{col 59}Yes
{col 5}{cmd:layout()}, {cmd:tabs()} and{col 38}Yes{col 59}Yes
{col 7}{cmd:filterposition()}
{col 5}Bootstrap {cmd:layout(bs)}{col 38}reflows{col 59}reflows
{col 5}Health endpoint{col 38}n/a{col 59}{cmd:/health}
{col 5}Script errors shown{col 38}status line{col 59}server log
{col 5}Who can open it{col 38}who has the file{col 59}who has its link
{col 5}Deployment{col 38}email, open file{col 59}{cmd:python app.py}
{col 5}{hline 72}

{pstd}
If the page's script fails during a move, a status line under the filters
says so (a screen reader announces it) and the browser console holds the
error.

{pstd}
{ul:What a filter move redraws.}  The saved page draws every layer that
plots observations -- scatter, line, area, bar, spike, dropline, the range
and paired-coordinate plots, and their marker labels -- from the rows that
pass the filter, each from its own rows among them, a line still in its join order.  It
recounts a histogram's
bars, and re-estimates a density on its grid, from the rows that pass the
filter -- for a {cmd:by()} panel, or a graph or plot with its own {cmd:if}
or {cmd:in}, from its own rows among them -- and keeps the bin edges and the
grid chosen when the dashboard was built, so neither moves as you filter
(a histogram or density drawn by {cmd:recast()} as {cmd:scatter},
{cmd:line}, {cmd:connected}, {cmd:area}, {cmd:bar}, {cmd:spike} or
{cmd:dropline} is recounted after a move the same way); it
refits every fitted or smoothed line ({cmd:lfit}, {cmd:qfit},
{cmd:lfitci}, {cmd:qfitci}, {cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess},
{cmd:lpoly}, {cmd:lpolyci}, {cmd:mband}, {cmd:mspline}) from the rows that
pass the filter, with the notes below on lowess's operation cap and lpoly's
exact-fit bandwidth.  It does not refit a {cmd:recast()} fit, a band or
line {cmd:ciplot()} or {cmd:fitplot()} draws as another type, or a fit
computed by {opt estopts()}, {opt predopts()} or {opt estcmd()}, which is
Stata's and is marked "(unfiltered)" after a move.  A fractional-polynomial
fit and its band ({cmd:fpfit}, {cmd:fpfitci}) are refitted with
{cmd:fracpoly}'s degree-2 search over the kept rows, drawn at their distinct
x, the band at its {cmd:level()} with {cmd:stdp}.  The median bands and median spline ({cmd:mband}, {cmd:mspline})
are recomputed from the kept rows, the default number of bands following
their count as {cmd:twoway}'s does.  A straight or quadratic fit and its confidence band ({cmd:lfit},
{cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}) are refitted from the rows that
pass the filter, on {cmd:n()} points over their range or {cmd:range()},
the band at its {cmd:level()} with {cmd:stdp}, {cmd:stdf} or {cmd:stdr}.  A
{cmd:lowess} smooth is recomputed with Stata's algorithm; a page whose
smooth would take more than about half a second (over 200 million window
operations, about 15,000 rows at the default bandwidth) leaves the line
empty after a move rather than freezing the browser.  An {cmd:lpoly}
smooth and its confidence band ({cmd:lpolyci}, with {cmd:pwidth()} and
{cmd:var()}) are refitted with the default bandwidth recomputed from the
kept rows; where that bandwidth is Stata's round-off of an exact global fit (y
an exact polynomial in x, or no more rows than the rule of thumb's fit has
coefficients), which {cmd:dash serve} reproduces and the saved page cannot
reproduce on every machine, the saved page keeps the smooth and band it was
built with and marks the layer, as below.  When a move
removes observations such a line, a line the page does not refit, a
histogram's bins or a density's grid was computed from, the page marks the
layer: it is dimmed, its legend key reads
"(unfiltered)", "(bins unfiltered)" or "(grid unfiltered)", the graph shows
"Marked layers were computed before the filter", and a note under the
filters says the same in text a screen reader reads.  A density drawn over
{cmd:range()} keeps the grid you gave and is not marked; one without it
is drawn on the kept rows' grid, as {cmd:twoway} draws it, and is not
marked unless its variable is a date or it is drawn as {cmd:dot}.  A
{cmd:histogram} on {cmd:twoway}'s default grid is binned again over the
kept rows, as {cmd:twoway} bins them; one given {cmd:bin()},
{cmd:width()}, {cmd:start()} or {cmd:discrete}, or of a date, keeps its
bins and is marked.  A
{cmd:contour} or {cmd:contourline} is recomputed up to 1,000 distinct
points; above that it is kept as built and marked "(grid unfiltered)",
and the served app recomputes its surface.  The marks go when
the filters again keep every observation the layer was computed from; a move
that removes only observations the layer never used (a missing y, x or
weight, a zero weight, or one outside the plot's own {cmd:if} or {cmd:in})
marks nothing, and a graph {cmd:exclude()} protects is never marked.  The
served app draws every layer again from
the rows that pass the filter -- each layer from its own rows among them --
bins, grid and fitted line included.  A plot's own {cmd:if} or {cmd:in}
inside a linked {cmd:by()} panel, or inside a linked graph with its own
{cmd:if} or {cmd:in}, keeps to that panel's or graph's observations after
every move, in both.  In both, a filter move clears a
selection brushed on a graph it redraws, and a card that follows the brush
({cmd:update(brush)} or {cmd:update(both)}) then counts the rows that graph
shows.  In both, a layer that a filter, a {cmd:by()} panel or its own
{cmd:if} or {cmd:in} leaves with no observations keeps its colour, width and
legend key, as twoway draws it, and in silence: neither mode prints a note
for it, as {cmd:twoway} prints none.

{pstd}
{ul:What "reflow" means.}  A {cmd:layout(bs)} grid rearranges itself as the
browser window narrows, in both modes: a cell of four columns or fewer
takes half the row below 992 pixels, every cell takes the whole row below
768, and a KPI card's cell keeps a minimum height keyed to its span (130
pixels under six columns, 150 from six, 170 at twelve; 120 below 768).
Every other grid stacks the same way in both modes when it is too narrow
for its columns.  See {help dash##layout:Layout}.

{pstd}
{ul:Blocking behavior.}  {cmd:dash serve} blocks Stata until the server
stops.  {cmd:timeout(}{it:#}{cmd:)} stops it after {it:#} minutes, and the
command returns 0.  Break -- the Break button or menu item, or Ctrl+C in
console Stata -- stops it at once, and the command ends with r(1), as any
command interrupted by Break does.  If Stata exits, crashes or is killed,
the server stops by itself within a few seconds and frees its port
(measured on macOS; Linux and Windows have not been measured).  dash then
removes its temporary folder; see
{help dash##tempfiles:Temporary files and privacy}.

{pstd}
{cmd:dash serve} makes a new key for each launch.  Once the server answers
{cmd:/health} it prints the server's address and the path of a file,
readable only by you, holding the dashboard's link --
{cmd:http://127.0.0.1:}{it:port}{cmd:/?token=}{it:key} -- and, unless
{cmd:nobrowser}, {cmd:$dash_nobrowser} or a {cmd:nodraw} graph says not to,
opens that link in your browser.  The key itself is never printed, so no
Stata log holds it, with one exception: if no such file can be written
anywhere, {cmd:dash serve} prints a warning line and then the link itself,
once, and keeps serving.  The key is then in Results and in any log you have
open, so treat that log like the link.  Open the file, or copy the link from
it, to reach the dashboard again while the server runs; it is removed when
the server stops.  On a disk that keeps no file permissions the file is
written anyway, and a note, {cmd:(note: dash:} ...{cmd:)}, names it.

{pstd}
If no server starts -- the port is in use, or the app
stops before it answers -- {cmd:dash serve} says why and returns r(198)
instead of blocking.

{pstd}
{ul:Notes.}  {cmd:dash build, server} prints the notes {cmd:dash build}
prints for a saved page -- an option it draws differently, a fit
{cmd:twoway} could not fit, a {cmd:by()} sub-option it ignores -- in the
same {cmd:(note: dash:} ...{cmd:)} form, once each: after writing the app it
draws the dashboard once, as a session of the app would, and names what
that drawing noted.  This costs one more drawing of the dashboard.  If that
drawing fails, a note says so, and the app is still written.
{cmd:dash serve} prints its build's notes at once and, while it serves,
the app's own notes, error lines and Python tracebacks: each note once,
never one its build already printed, at most 100 notes and 200 other lines,
with the link's key and every query string removed.  The app's notes
appear when the first session draws the dashboard.  Run as
{cmd:python app.py} or under {cmd:bokeh serve}, the app prints each note
once per process on its standard error, as {cmd:(note: dash:} ...{cmd:)},
whatever Python's warnings filters or {cmd:PYTHONWARNINGS} say.

{pstd}
{ul:Running the generated .py file independently.}
{cmd:dash build, saving(app.py) server} writes a self-contained server app
that embeds, base64-encoded, every observation of the variables the
dashboard uses.  dash writes it readable only by you (0600); see
{help dash##tempfiles:Temporary files and privacy}.  When you run the file
yourself, with {cmd:python} or {cmd:bokeh serve}, Python opens it by its name
and imports modules from the folder that holds it, so keep it in a folder
only you can write.  {cmd:dash serve} does not run its own copy that way: it
hands Python the text it wrote and checked.  Run it outside Stata with:

{phang2}{cmd:python app.py}{p_end}

{pstd}
It accepts {cmd:--port} {it:N}, {cmd:--address} {it:iface},
{cmd:--allow-websocket-origin} {it:host:port} (repeatable),
{cmd:--timeout} {it:minutes}, {cmd:--show}, {cmd:--trust-forwarded-for}, and
the rate limits {cmd:--sessions-per-client} {it:N},
{cmd:--new-clients-per-minute} {it:N} and {cmd:--sessions-per-minute}
{it:N} described below, and {cmd:--max-sessions} {it:N} and
{cmd:--idle-timeout} {it:minutes} (see
{help dash##limits:Resource limits}).  No browser window opens unless
{cmd:--show} is given, so the app is usable from a script or a batch job.

{pstd}
The app never runs without a key, and only a link holding it opens the
dashboard: {cmd:http://127.0.0.1:}{it:N}{cmd:/?token=}{it:key}.  Unless you
choose the key, each start makes a new one, writes that link to a file named
{cmd:link.html}, readable only by you, in a new folder only you can open,
and prints the file's path on a line of its own before the server starts;
the key itself is never printed.  Open the file, or copy the link from it;
the folder is removed when the app stops.  On a disk that keeps no file
permissions the file is written anyway, and a note,
{cmd:(note: dash:} ...{cmd:)}, names it; set {cmd:TMPDIR} to a folder on a disk that
keeps them.  If no such file can be written at all, the app
prints a warning line and then the link itself, once, and keeps serving; the
key is then in that output and in any log of it.  To choose the key, set the
environment variable {cmd:DASH_SERVE_TOKEN} to 32 to 128 of the characters
A-Z, a-z, 0-9, _ and -, or pass {cmd:--token-stdin} and write it as one line
on standard input; the app then writes no link file.  A value of any other
form stops the app at once (exit status 2), naming the variable but not the
value.

{pstd}
{cmd:--port} outside 1024 to 65535 is refused (exit status 2), not moved
to the nearest port.

{pstd}
{cmd:bokeh serve app.py} also serves the dashboard, but as {cmd:bokeh serve}'s
own application, and so without what the app's own server adds: there is no
{cmd:/health}, a session's dashboard is drawn on the server's event loop
(see below), none of the headers below is sent, the session limits below
do not apply ({cmd:bokeh serve} runs the script afresh for each session, so
every session starts a new count), and the app's flags above are not read.
The session cap, the idle close, the data decoded once and the memo of the
slow fits do apply there, per process under {cmd:--num-procs}, set by the
environment variables {cmd:DASH_MAX_SESSIONS} and {cmd:DASH_IDLE_TIMEOUT}
(digits only; any other value stops the app); a session past the cap shows
the busy text as its page, sent with status 200.
{cmd:bokeh serve} takes its own {cmd:--port}, {cmd:--address} and
{cmd:--allow-websocket-origin}, and listens on every interface unless it is
given {cmd:--address}.
Under {cmd:bokeh serve} the app still never runs without a key.  Start it as
{cmd:bokeh serve app.py --allow-websocket-origin 127.0.0.1:5006}: Bokeh
otherwise admits only {cmd:localhost}, and the link's page stays blank.
With {cmd:DASH_SERVE_TOKEN} set as above, open
{cmd:http://127.0.0.1:5006/app?token=}{it:key}.  Without it, the app makes
one key for the server when the first session is asked for, and at the first
page request writes
{cmd:http://127.0.0.1:}{it:port}{cmd:/app?token=}{it:key} to a
{cmd:link.html} only you can read and prints that file's path (if no such
file can be written, it prints a warning line and then the link itself, once
for each app); the folder is removed when {cmd:bokeh serve} stops.  Every
session without the key gets a page saying where the link is and naming
{cmd:DASH_SERVE_TOKEN}.  {cmd:bokeh serve --show} opens the address without
the key, so it shows that page and makes the link: open the file it names.
The link names no {cmd:--prefix}, and a session asked for only through
{cmd:bokeh.client} leaves the link to the first page request.

{pstd}
{ul:Security.}  Run as {cmd:python app.py}, or by {cmd:dash serve}, the app
binds the loopback interface, so by default only programs on this machine
can reach it, and of those only one holding the dashboard's link opens it:
every page, session, {cmd:/autoload.js} and {cmd:/metadata} request without
the link's key is refused (403) before any data is read.  The key is new at
every launch, is compared in constant time, and travels only in the link's
{cmd:?token=}; {cmd:/health} and BokehJS's own files under {cmd:/static}
stay open and hold no data.
{cmd:--address} {it:addr} opens it deliberately
-- {cmd:--address 0.0.0.0} listens on every interface -- and
{cmd:--allow-websocket-origin} {it:host:port} then admits the {cmd:Origin}
values a browser will send from there.  The files {cmd:dash serve} writes are
readable only by you wherever your disk keeps permissions, and dash notes any
location where they are not; see
{help dash##tempfiles:Temporary files and privacy}.

{pstd}
Understand what that second option is, before relying on it.  The
{cmd:Origin} allow-list filters a header the {it:client} supplies, so it
stops a page on another website from driving your dashboard in your browser.
It is not an access control: a client that is not a browser can omit the
header or forge an accepted one.  The dashboard's key is the access control: a client without it gets nothing,
whatever {cmd:Origin} it sends.

{pstd}
An origin is admitted only when its host matches an allowed one label for
label: {cmd:localhost.example.com} is not {cmd:localhost}.  Bokeh before 3.9
matched only the first labels, so a page from any name that begins with an
allowed host was admitted; the app checks origins itself whatever Bokeh it
runs under, and says so when it starts under such a Bokeh.
{cmd:bokeh serve app.py} makes Bokeh's check exact in the same way for
every session, and {cmd:dash} notes any bokeh newer than it was verified on.

{pstd}
If a bokeh release changes what this protection relies on -- the page
template's blocks, the origin matcher, the key check's hook or its token
layout -- the app refuses to start ({cmd:python app.py}) or refuses each
session ({cmd:bokeh serve}) with a message naming it, and a saved page is
not written; {helpb dash_setup} installs a verified bokeh.

{pstd}
Bokeh's environment variable {cmd:BOKEH_ALLOW_WS_ORIGIN}, when it is set,
replaces that allow-list: Bokeh admits the origins it names {it:instead of}
{cmd:localhost}, {cmd:127.0.0.1} and {cmd:--allow-websocket-origin}.  The
app says so when it starts, naming them, and warns when the variable holds
{cmd:*}: the origin check then admits every website, and only the
dashboard's key keeps another site's page out.  Unset it to have the app's
own list apply.

{pstd}
Environment.  The app serves BokehJS from its own {cmd:/static}, so
{cmd:BOKEH_RESOURCES} set to anything but {cmd:server} or {cmd:inline} --
{cmd:cdn}, say, which the page's policy would not let load -- stops
{cmd:python app.py} before it builds anything, with exit status 2 and one
sentence naming the value; unset it and start again.  {cmd:BOKEH_MINIFIED}
and {cmd:BOKEH_DEV} are honoured: when they choose Bokeh's unminified or
development bundle, {cmd:dash build} (once a command) and the served app
(once a process) say so, since the page is then larger than the shipped one;
it behaves the same.  {cmd:/health} answers with JSON holding
{cmd:status}, {cmd:timestamp}, {cmd:sessions} (the sessions open now),
{cmd:max_sessions} (the limit), {cmd:bokeh} and {cmd:dash} (the two
versions) and {cmd:uptime_s} (whole seconds since the app started), and
nothing else: no data, no paths and nothing from the request.  When the
browser command that opens a saved page fails, dash prints its return code
and the page's path, so you can open it yourself.

{pstd}
The generated app embeds every observation of the variables the dashboard
uses, and anyone who holds its link can read them.  The key is in the link,
so it is wherever the link is: the browser's address bar and history, the
file {cmd:dash serve}, {cmd:python app.py} or {cmd:bokeh serve} names, the
output and any log where one of them printed it because no file could be
written, and anything you paste it into.  Treat the link as a password while
the server runs; a new launch makes a new key, and the old link stops
working.  The key travels in plain HTTP: on loopback that stays on this
machine, but with {cmd:--address} beyond loopback anyone who can watch the
network can read it, so reach such a server through an SSH tunnel or a
reverse proxy that adds TLS.  The browser is handed the link without it
appearing on any command line: on macOS through {cmd:osascript}'s standard
input, elsewhere (or when {cmd:BROWSER} is set) through a page only you can
read that forwards to it.  Linux and Windows have not been tested.

{pstd}
Within the file, data values are base64-encoded so that no data content can
affect the Python source's syntax, and every user-supplied string reaches
the page as a Bokeh model property or as escaped text inside the markup dash
writes, never as markup of its own.
An image panel shows an SVG file that dash has checked, inside an image
element, which runs no script; its only link is the {cmd:link()} page in
the same folder.
Text drawn on a graph -- a title, subtitle, note, caption, axis title,
tick label, legend key, {cmd:by()} panel title or colour key -- is never
handed to a TeX engine: {cmd:$$}, {cmd:\(} and {cmd:\[} in it are drawn
as typed, as {cmd:twoway} draws them, in a saved page and a served one.

{pstd}
The page carries a Content-Security-Policy in both modes, and the policy
decides which scripts the browser runs.  A saved dashboard runs only the
scripts dash wrote into it, each named in its policy by its SHA-256 hash,
and loads nothing from anywhere; dash refuses to write a saved page holding
an inline script it did not name.  A served page runs only the scripts that
carry that page's nonce, a random value the server makes for each page it
sends, and may also load from, and connect to, the server it came from, and
nothing else.  So a script or an event handler that reached a page some
other way -- through a fault in escaping, say -- does not run.  Two
allowances remain, because BokehJS needs them: {cmd:'unsafe-eval'}, since
Bokeh compiles each filter callback, tick formatter and tooltip formatter
with {cmd:new Function}, and inline styles, since BokehJS writes its styles
as it draws.  The policy is no substitute for escaping, which dash does for
every string you give it, and a browser that supports only the first version
of the standard (CSP level 1) shows a blank page.  The page that forwards
your browser to a served dashboard, and the page written when a dashboard
has nothing to show, carry {cmd:default-src 'none'}: they run no script at
all.  {cmd:python app.py} also sends a policy as a header on every response,
{cmd:/health} included, adding {cmd:frame-ancestors 'none'} so that no other
site can frame the dashboard, and sends
{cmd:X-Content-Type-Options: nosniff}, {cmd:X-Frame-Options: DENY} and
{cmd:Referrer-Policy: no-referrer} with it.  That header cannot know each
page's nonce, so it keeps {cmd:'unsafe-inline'}; a browser applies both
policies, and the page's own refuses an injected script.
{cmd:bokeh serve app.py} sends none of these headers, so its page carries
the policy but can be framed.

{pstd}
A saved page can be shown inside another page with an {cmd:<iframe>}: its
policy, carried in the page itself, has no {cmd:frame-ancestors} directive
(a browser ignores that directive in a page's own policy), so any page may
frame it.  A dashboard served by {cmd:python app.py} cannot be framed: its
headers send {cmd:frame-ancestors 'none'} and
{cmd:X-Frame-Options: DENY}.

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
Each takes a whole number from 1 to 1,000,000.  A session over a limit is
served a page that reads {cmd:429 Too Many Requests} in place of the
dashboard -- the page itself arrives with HTTP status 200, as Bokeh sends
every page -- and a {cmd:/health} request over its own limit is answered
with status 429.  The server logs a limit's refusals at most once a
minute, so a flood cannot flood the log: each line names the limit and,
for a session limit, its flag, and counts the ones refused since its
last line.  No client that is still active is ever forgotten to make
room for new ones, so a flood of addresses cannot reset a real client's
count.

{pstd}
{ul:Recomputation.}  A slider recomputes the dashboard when you release
it, not at every step of the drag, in the served app and on the saved page.
In each browser session, each filter widget and each brushed data source
then recomputes at most 10 times in a burst and twice a second after that;
changes that arrive faster are folded into one recomputation with the
latest values.  A script that moves a widget in a loop is therefore held to
that rate.  Recomputations run on one worker thread per server process,
one at a time and in the order sessions asked; meanwhile the page shows
"Updating..." and keeps its drawing, and other sessions and {cmd:/health}
keep answering.  A newer move replaces a session's waiting one, and a
result a newer move overtook is discarded.  The longest wait is about the
session limit times one recomputation: about 3 minutes with 20 sessions
for {cmd:lowess} at 100,000 observations.  Opening a session still pauses
the server while its page is built.

{pstd}
{ul:What still differs.}  The two pages are laid out alike: both declare a
viewport for phones, both dim the unselected points of linked graphs to
15% when a brush is drawn, and a {cmd:layout(bs)} grid takes the same half
rows and KPI cell heights in both.  One difference remains, recorded and
not changed: under {cmd:layout(bs)} with {cmd:filterposition(left)}, the
saved page draws the title and subtitle inside the content column beside
the filter sidebar, where the served app draws them above the sidebar and
the content together.

{pstd}
The generated app embeds every observation of the variables the dashboard
uses, base64-encoded.  Treat the {cmd:.py} file as you would the data:
{cmd:dash serve} writes its copy into a folder only you can open, erases the
specification and data once the application is written, and the application
once the server answers; only a crash in the seconds before the server
answers can leave a private copy, which the next dash command removes.  A
file you name with {cmd:saving()} is written readable only by you (0600) and
is yours to manage.  A browser receives only the observations the dashboard
draws or filters, as a saved page holds them, numbered as the saved page
numbers them, so no row number shows where an excluded observation was; the
{cmd:.py} file and its data still hold every observation.


{marker tempfiles}{...}
{title:Temporary files and privacy}

{pstd}
{ul:Run folders.}  Each render's specification and data go into a folder
{cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/run-}{it:pid}{cmd:-}{it:random},
which only you can open (0700), in files only you can read (0600).  dash
removes the folder when the command ends.  A folder left by an error,
Break, a crash or a killed Stata is removed by the next dash command of that
session, or by any session once that Stata has ended (on Windows, after a
day).

{pstd}
{ul:dash serve.}  {cmd:dash serve} writes its application there and erases
the specification and data once the application is written, and the
application once the server answers, so no copy of the data stays on disk
while the server runs; only a crash in the seconds before the server answers
can leave a private copy, which the next dash command removes.

{pstd}
{ul:Previews.}  The one-line form's pages go to
{cmd:c(tmpdir)}{cmd:dash-}{it:uid}{cmd:/previews/} under unique names,
readable only by you.  The newest five of a session are kept, and
{cmd:dash clear} removes the session's pages except one a browser was asked
to open in the last minute.

{pstd}
{ul:When a location is not private.}  dash never stops a command for
privacy.  If {cmd:c(tmpdir)} can be changed by other accounts (others can
write to it and it has no sticky bit, as a {cmd:STATATMP} folder made under
umask 002 has, or it belongs to another account), if a {cmd:dash-}{it:uid}
there is a link, not a folder or another account's, or if your disk will not
keep a folder private, dash goes on: it writes each file readable only by
you wherever the disk allows and prints one note per command,
{cmd:(note: dash:} ...{cmd:)}, that names the location and the remedy -- {cmd:chmod go-w}
on the folder, or starting Stata with {cmd:STATATMP} set to a folder only you
can write.  A {cmd:dash-}{it:uid} dash cannot use is left alone: dash keeps
its copies in a folder {cmd:dash-}{it:uid}{cmd:-}{it:xxxxxxxx} beside it that
only you can open, and the note names both.  Like {cmd:dash}'s other notes,
it is shown under {cmd:quietly} and hidden by {cmd:capture}.  Only {cmd:c(tmpdir)} itself is checked,
not the folders above it.  In a {cmd:c(tmpdir)} others can write without a
sticky bit, another account could move dash's folders, though not read the
files in them.  It cannot change what {cmd:dash serve} runs: dash does not
start its application by name, but opens the file it wrote, checks that it
is that file with the same contents, and hands the text to Python itself, so
a file swapped in afterwards is never run, and no module beside it or in your
working folder is imported (measured on macOS; Linux and Windows have not
been measured).  Such an account could still replace the specification or
data between their writing and their reading, or keep the server from
starting.

{pstd}
{ul:A guard against planted names.}  This guard does not depend on privacy.
dash never writes through a symbolic link, into a pipe or device, over a
file with other hard links or over another account's file, and never runs an
application other than the one it wrote; in each case it stops with
r(7102) and names the path.  If dash cannot create its folder at all
({cmd:c(tmpdir)} missing, read-only or full), it stops with r(603), as
Stata's own file commands do.

{pstd}
{ul:Named files.}  A page you name with {cmd:saving()} is written with your
umask, as twoway's {cmd:saving()} and {cmd:graph export} write theirs
(usually 0644); it embeds the data.  The server app that {cmd:dash build}
writes with {cmd:server} to the {cmd:.py} file you name in {cmd:saving()}
also embeds every observation, so it is written readable only by you (0600),
whatever your umask.  If your disk does not keep that permission, dash still writes the
file and prints a note naming it.  {cmd:replace} writes a new file rather
than rewriting the old one.  As a guard against a planted name, dash
refuses, r(7102), a symbolic link or another account's file at that name,
and never writes to a link's target.  The folder you name keeps its own
permissions: dash neither refuses nor notes a folder of yours that others
can read, so choose one other accounts cannot list if the file's name is
itself private.

{pstd}
{ul:Stata's own files and Windows.}  Stata's own temporary files (a
{cmd:preserve} larger than {cmd:max_preservemem}, for instance) follow your
umask.  On Windows, privacy rests on your per-user TEMP folder, which has not
been tested.


{pstd}
{ul:Page size.}  Each distinct display format on a page carries one tick
formatter and one tooltip formatter of about 38 KB each, the writer that
writes numbers and dates as Stata's {cmd:display} does; the page's script
cannot share one model between an axis and a tooltip, so a page with many
formats grows by that much for each.

{marker limits}
{title:Resource limits}

{pstd}
The quantities below decide how much {cmd:dash} builds -- the graphs in the
registry and the plots in a graph, the panels of a {cmd:by()} graph, and
the tabs, filters, dropdown values, reference lines, added texts and table
rows a dashboard draws -- and each has a limit.  Each limit has a default,
a ceiling that nothing moves, and a global macro that moves it for the rest
of the session:

{synoptset 28 tabbed}{...}
{synopthdr:global}
{synoptline}
{synopt:{cmd:$dash_max_graphs}}graphs and KPI cards in the registry; default
    100, at most 1,000.  A new name past it is refused with
    {cmd:r(134)}.  It also bounds the cells of a {cmd:layout()} grid, which
    is refused with {cmd:r(198)} when larger.{p_end}
{synopt:{cmd:$dash_max_images}}image panels in the registry; default 100, at most 1,000.  Over it {cmd:dash image} is refused with {cmd:r(134)}.{p_end}
{synopt:{cmd:$dash_max_plots}}plots in one graph, where each y variable of
    {cmd:scatter y1 y2 x} is one; default 100, at most 1,000.  Refused with
    {cmd:r(134)}.{p_end}
{synopt:{cmd:$dash_max_filter_options}}values one {cmd:type(dropdown)}
    filter lists; default 1,000, at most 100,000.  Over it a numeric or date
    variable is drawn as {cmd:type(range)} and a string variable lists its
    first values in sort order.{p_end}
{synopt:{cmd:$dash_max_by_groups}}groups one {cmd:by()} graph draws, a panel
    each, and its {cmd:total} panel one more; default 100, at most 1,000.
    The first groups in sort order are drawn.{p_end}
{synopt:{cmd:$dash_max_tabs}}tabs; default 50, at most 500.  The first are
    drawn.{p_end}
{synopt:{cmd:$dash_max_filters}}filter widgets; default 20, at most 200.
    The first are built.{p_end}
{synopt:{cmd:$dash_max_reflines}}reference lines over the dashboard: the
    positions of every {cmd:xline()} and {cmd:yline()}, on either axis,
    times the graph's {cmd:by()} panels, counted over every
    observation; default 10,000, at most 100,000.  Refused with
    {cmd:r(134)}.{p_end}
{synopt:{cmd:$dash_max_added_text}}added texts: the points of every
    {cmd:text()} times the graph's {cmd:by()} panels, in one graph and over
    the dashboard; default 1,000, at most 100,000.  Refused with
    {cmd:r(134)}.{p_end}
{synopt:{cmd:$dash_max_table_rows}}rows a graph's {help dash##table:data table}
    lists when {cmd:table()} gives no {cmd:rows()}; default 1,000, at most
    100,000.  The first drawn rows are listed, with a note.{p_end}
{synoptline}

{pstd}
A limit that clamps says so in a note naming the limit and the global that
raises it; a limit that refuses says so in its error.  For example,

{phang2}{cmd:. global dash_max_by_groups 250}{p_end}

{pstd}
lets one {cmd:by()} graph draw 250 groups.  A global must be a whole number
from 1 to its ceiling, written in digits; anything else is refused with
{cmd:r(198)}.  An unset global means the default.  {cmd:dash clear} does not
drop these globals, because they are settings rather than registry;
{cmd:macro drop dash_max_*} does.

{pstd}
{ul:No size limit.}  {cmd:dash} sets no limit on the size of a dashboard:
it embeds every value its graphs, cards and filters need, however many, in
a saved page and in a served app.  Above 1,000,000 embedded values it notes
the size the file will be, at about 24 bytes a value, which is what a saved
page takes; a served app's file carries the values as text and takes up to
about twice that.  Measured, 4,000,000 values made a 95 MB page and took
about 2 GB of memory to render, and Chrome, the browser dash is tested in,
cannot hold a page much past 512 MB.  To make a page smaller, reduce the
data first -- {cmd:keep}, {cmd:drop}, {cmd:sample} or {cmd:collapse},
inside {cmd:preserve} and {cmd:restore}.

{pstd}
{ul:WebGL.}  A graph that draws more than 10,000 rows is drawn with WebGL,
which is faster for many points, unless it draws a dashed, dotted or
patterned line, which WebGL breaks up: such a graph is drawn on the
ordinary canvas.  The rows counted are the graph's own -- the rows its
qualifiers select, or its {cmd:by()} panel's -- not the dataset's.

{pstd}
{ul:A served dashboard} has rate limits of its own; see
{help dash##server_mode:Server Mode}.

{pstd}
{ul:Sessions open at once.}  A served app holds at most
{cmd:maxsessions()} sessions open at once ({cmd:--max-sessions},
{cmd:DASH_MAX_SESSIONS}; default 20).  A page asked for beyond it, by a
client that holds the key, gets HTTP 503 with {cmd:Retry-After: 30} and a
fixed text that names the setting, with no script and no refresh; a client
without the key still gets 403.  A closed tab frees its place within about
20 seconds.  A session with no filter move, brush or CSV download for
{cmd:idletimeout()} minutes ({cmd:--idle-timeout}, {cmd:DASH_IDLE_TIMEOUT};
default 60, 0 never) is closed: its page says so and frees its place, so a
tab that was only being looked at can need a reload.  The data is decoded
once per app process and shared, read-only, by every session, and the
lowess, fpfit and lpoly fits are kept for reuse within 64 MB per process.
Each session's memory grows with the rows and layers it draws, and dash sets
no bound on it (about 70 MB at 200,000 rows and one scatter, about 150 MB
with three), so set {cmd:maxsessions()} to fit the machine and the data.  Before it listens the app
prints {cmd:preparing the dashboard (}{it:N} {cmd:rows, }...{cmd:)} and
draws the dashboard once, so a long start is not a failure and no reader
pays for the first drawing.  Under {cmd:dash serve} and {cmd:python app.py}
a new session's dashboard is drawn off the server's event loop, two at a
time, so the server answers other readers meanwhile.
{cmd:dash serve} and {cmd:python app.py} are the supported way to serve the
dashboard; under {cmd:bokeh serve} each session's dashboard is drawn on the
loop, and other readers wait while it is drawn: Bokeh (3.8 and 3.9) runs a
script app afresh for each session on its loop and gives it no hook to run
first, and it never runs an async {cmd:on_session_created} of a directory
app's {cmd:server_lifecycle.py} (a plain one runs on the loop).

{pstd}
Building a page inside Stata asks Stata's own tick routine for at most 256
axis ranges; any further range is ticked by the model.  {cmd:dash serve} and
{cmd:dash build, server} draw the figures once more inside Stata to ask for
them, which adds 4.4 seconds to a served build of 1,000,000 observations
(11.0 seconds in all) on the tested platform.


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

{pstd}{ul:Live Bokeh Server (blocking — Break to stop)}{p_end}
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
Each value of {it:varlist} -- each combination of values, with several
variables -- produces a separate panel of the observations in that group.
Observations with a missing {cmd:by()} value -- a string variable's {cmd:""}
included, as in {cmd:twoway} -- are left out unless {cmd:missing} is given.

{synoptset 30}{...}
{synopt:{opt by(varlist)}}facet graph by the values of {it:varlist}{p_end}
{synopt:{opt by(varlist, cols(#))}}arrange facet panels in {it:#}
    columns{p_end}
{synopt:{opt by(varlist, rows(#))}}arrange facet panels in {it:#}
    rows; abbreviation {cmd:r()}{p_end}
{synopt:{opt by(varlist, holes(numlist))}}leave the cells numbered in
    {it:numlist} empty; abbreviation {cmd:hol()}{p_end}
{synopt:{opt by(varlist, colfirst)}}fill the cells down the columns;
    abbreviation {cmd:colf}{p_end}
{synopt:{opt by(varlist, compact)}}no space between the panels;
    {cmd:style(compact)} too{p_end}
{synopt:{opt by(varlist, iscale([*]#))}}size the panels' text, markers and
    lines; {cmd:*}{it:#} multiplies the default{p_end}
{synopt:{opt by(varlist, imargin(marginstyle))}}the space around each
    panel; abbreviation {cmd:im()}{p_end}
{synopt:{opt by(varlist, total)}}add a "Total" panel of every group's
    observations{p_end}
{synopt:{opt by(varlist, missing)}}include a panel, titled "(missing)", of
    the observations with a missing value (a string variable's ""
    included){p_end}
{synopt:{opt by(varlist, title() subtitle() note() caption())}}drawn once
    over the panels; abbreviations {cmd:ti}, {cmd:sub}, {cmd:note},
    {cmd:cap}{p_end}
{synopt:{opt by(varlist, note(""))}}remove the "Graphs by" note{p_end}
{synopt:{opt by(varlist, yrescale|xrescale|rescale)}}draw each panel on its
    own y scale, x scale or both; abbreviations {cmd:yr}, {cmd:xr} and
    {cmd:r}, and {cmd:noyrescale}, {cmd:noxrescale} and {cmd:norescale}
    ({cmd:noyr}, {cmd:noxr}, {cmd:nor}) to keep one scale; when both are
    given, the rescale wins, as in {cmd:twoway}{p_end}
{synopt:{opt by(varlist, style(rescale))}}and style(combine): only
    their separate scales are drawn, with a note{p_end}
{synopt:{opt by(varlist, iyaxes ixaxes)}}draw every panel's y or x axis;
    {cmd:iylabels}, {cmd:iyticks}, {cmd:iytitles} and their x and
    {cmd:no} forms, {cmd:individual}{p_end}
{synopt:{opt by(varlist, noedgelabel)}}draw x axes on the bottom row and y
    axes on the left column only; {cmd:edgelabel}{p_end}
{synopt:{opt by(varlist, noytitles noxtitles)}}leave out the axis titles
    drawn beside and below the panels{p_end}
{synopt:{opt by(varlist, legend())}}place the one legend:
    {cmd:position()}, {cmd:at()}, {cmd:on}, {cmd:off}; beside the panels
    it is placed along its side on the panels and their axes, as in
    {cmd:twoway} (at 6 o'clock centred under them, at 3 beside their
    middle), and with {cmd:span} on the whole graph; in an {cmd:at()}
    hole at its {cmd:position()}'s compass in the hole{p_end}
{synopt:{opt by(varlist, ilegends)}}a legend on each panel instead{p_end}
{synopt:{opt by(varlist, clegend(on))}}one colour key, the first
    panel's; {cmd:position()}, {cmd:at()}{p_end}
{synoptline}

{pstd}
As in {cmd:twoway}, a {cmd:by()} graph's panels share one scale per axis --
y, x and a second axis -- spanning every panel's data, the Total panel's
too, and they keep sharing it after a filter move.  Panning or zooming one
panel moves the others; a filter move spans the axes again over the rows kept.  With {cmd:yrescale}, {cmd:xrescale} or
{cmd:rescale} each panel is drawn and ticked ({cmd:#}{it:N}) over its own
data on that axis; there {cmd:yscale(range())} and {cmd:xscale(range())},
those of the second axis included, are not applied, as in {cmd:twoway},
and a note says so; labels and ticks still widen each panel, and reverse
and log are kept.

{pstd}
The panels share their axes and keys as {cmd:twoway}'s do, in both modes and
after every filter move.  A y axis is drawn on the leftmost panel of each
row, an x axis under the lowest panel of each column (a panel above an
empty cell keeps its own), and a second y axis on the rightmost panel; with
{cmd:noedgelabel} or {cmd:compact} only the panels on the outer edge of the
grid draw them.  {cmd:iyaxes} and {cmd:ixaxes} draw every panel's axis, as
a rescaled axis is drawn, {cmd:noiylabels} and {cmd:noiyticks} (and their x
forms) take the labels or ticks off every axis, {cmd:individual} draws
none, and a word and its {cmd:no} form given together read as the word, as
in {cmd:twoway}.  The y and x axis titles are drawn once, beside and below
the panels, from the first panel, unless {cmd:noytitles} or
{cmd:noxtitles}; {cmd:iytitles} and {cmd:ixtitles} keep them on each
drawn axis too; no panel draws a second axis's title.  One legend, of the
first panel's keys as {cmd:legend()} orders and labels them, is drawn when
the first panel has more than one key or with {cmd:by(, legend(on))}, and
not with {cmd:by(, legend(off))}; it is placed by
{cmd:by(, legend(position()))}, in the cell {cmd:at(}{it:#}{cmd:)} names
(which counts as a cell of the grid, as in {cmd:twoway}), or else where the
scheme puts it (s2color below, stcolor right, economist above).
{cmd:ilegends} draws each panel's legend instead; {cmd:legend(on)} outside
{cmd:by()} draws both, and {cmd:legend(off)} outside {cmd:by()} changes
nothing, as {cmd:twoway} ignores it.  {cmd:by(, legend(ring(0)))} is drawn
as {cmd:twoway} draws it: outside the panels on its position's side, aligned
at that position's corner ({cmd:pos(5)} at the right, as a corner
{cmd:position()} is without {cmd:ring(0)} too), and below or left of the
panels between them and the axis title, which the default legend sits
beyond; {cmd:ring(1)} is drawn the same, and with no {cmd:ring()} the
scheme's {cmd:gridringstyle by_legend_ring} is read as one.  Clicking a key of
the overall legend hides that series in every panel.
Under {cmd:colorvar()} no colour key is drawn unless
{cmd:by(, clegend(on))}, which draws one, the first panel's, placed by
{cmd:clegend(position() at())} else the scheme's position, upright at
every position as in {cmd:twoway} (at 6 or 12 o'clock half the graph's
height less a sixth of its smaller side long).  On a narrow
screen, where the panels stack into one column, every panel shows its axes
and titles again, and {cmd:twoway}'s layout returns when the page widens.

{pstd}
The Total panel draws the observations of every group, as {cmd:twoway}'s
does: those with a missing {cmd:by()} value only with {cmd:missing}, a
string variable's {cmd:""} counted as missing in the groups and in Total.
The missing panel is titled "(missing)", as in {cmd:twoway}.

{pstd}
The panels are arranged the same way wherever the graph is drawn -- in the
dashboard's grid, in a tab, or in a {cmd:layout(bs)} cell -- and in both
{cmd:dash build} and {cmd:dash serve}: in the cells {cmd:twoway} places
them in, with {cmd:cols(}{it:#}{cmd:)} or {cmd:rows(}{it:#}{cmd:)}, and
otherwise in as many columns as the square root of the panels and
{cmd:holes()} rounded up, filled along the rows ({cmd:colfirst}: down the
columns), a hole's cell skipped.  As in {cmd:twoway}, a row or column that
holds no panel is not drawn, so {cmd:cols()} of more columns than there
are panels puts them all in one row; a {cmd:cols()} or {cmd:rows()} above
the {cmd:$dash_max_by_groups} limit is drawn at the limit, with a note.
Panel text, markers and lines are
drawn at {cmd:twoway}'s {cmd:by()} size -- 0.85 of the plain graph's for
2 to 4 panels, 0.6 for 10 to 16 -- or at {cmd:iscale()}; the overall
title, subtitle, note and caption are not scaled.  The space between the
panels is the scheme's {cmd:by()} margin, none with {cmd:compact}, or
{cmd:imargin()}.  {cmd:by()} arguments {cmd:twoway} refuses are refused
in its words and order: {cmd:rows()} with {cmd:cols()}, a {cmd:rows()},
{cmd:cols()} or {cmd:holes()} that is not positive integers, a repeated
or capitalised sub-option, an unknown one, and {cmd:iscale()} below 0 or
above 10,000.

{pstd}
A panel is labelled with its value's label, when the value has one, and
otherwise with the value as {cmd:twoway} writes it -- {cmd:3}, {cmd:.25} --
whatever its display format; a string variable's panels are labelled with
their text, and a date variable's with their dates in its display format
({cmd:01jan2000}, {cmd:2000m1}), where {cmd:twoway} writes the number
({cmd:14610}).  Several {cmd:by()} variables produce composite labels,
"Domestic, 3", as in {cmd:twoway}.  The label is drawn as its own centred
row under the graph's {cmd:title()}, which every panel keeps.  A graph's
{cmd:subtitle()} replaces the label, leads it with {cmd:prefix}, follows
it with {cmd:suffix}, and {cmd:subtitle("")} removes it.  A value label
holding double quotes stays one line, where {cmd:twoway} splits it.
As in {cmd:twoway}, the label is drawn in the scheme's filled box across
the top of the panel's plot region (s2color bluish gray, stcolor light gray,
s1color khaki outlined in black), the Total panel's too; {cmd:subtitle()}'s
{cmd:fcolor()}, {cmd:lcolor()} and {cmd:nobox} do not restyle it in
{cmd:dash} and are named in a note.
{cmd:by()}'s own {cmd:title()}, {cmd:subtitle()}, {cmd:note()} and
{cmd:caption()} are drawn once over the panels, placed on the panels and
their axes as in {cmd:twoway} (a title centred over them, a note at
their left, a caption at 5 o'clock ending at their right, each its text
box's margin in; with
{cmd:span} on the whole graph), and under them the note
"Graphs by" names the variables as {cmd:twoway} does: their labels,
"A and B" for two, and for three or more the first by its name
("Graphs by foreign, Repair record 1978, and Headroom (in.)").
One graph draws at most 100 groups by default, a panel each, and its Total
panel one more: over that, the first 100 groups in sort order are drawn and
a note names the limit and the global that raises it (see
{help dash##limits:Resource limits}).
{cmd:cols()}, {cmd:rows()}, {cmd:holes()}, {cmd:colfirst},
{cmd:compact}, {cmd:style(compact)}, {cmd:iscale()}, {cmd:imargin()},
{cmd:total}, {cmd:missing}, the rescale forms above, {cmd:title()},
{cmd:subtitle()}, {cmd:note()} and {cmd:caption()}, the axis and title
words above, {cmd:edgelabel}, {cmd:individual}, {cmd:ilegends},
{cmd:legend()}, {cmd:clegend()}, {cmd:graphregion()}, {cmd:plotregion()},
{cmd:subtitleformat()}, {cmd:shrink}, {cmd:overallshrink},
{cmd:noshrink}, {cmd:noishrink}, {cmd:nooverallshrink}, {cmd:ishrink} and
{cmd:style(altleg)} (drawn as {cmd:style(default)}, as {cmd:twoway} draws
it) are the {cmd:by()} sub-options {cmd:dash} implements.
{cmd:shrink} and {cmd:overallshrink} draw the panels' markers, lines and
text smaller, by the share of the graph the panels keep once {cmd:by()}'s
own texts are set aside, as measured in {cmd:twoway} under {cmd:s2color}:
0.894 with none, less 0.039 for the note, 0.060 for a title, 0.048 for a
subtitle, 0.047 for a caption and 0.047 for each further line (so
{cmd:by(foreign, shrink)} draws them at 0.855 of their size); a {cmd:no}
form after them does not undo them, as in {cmd:twoway}.  {cmd:by(, graphregion())} colours the whole graph
region, replacing a {cmd:graphregion()} outside {cmd:by()}, which on a
{cmd:by()} graph colours nothing (as in {cmd:twoway}), and
{cmd:by(, plotregion())} the region around the panels, its fill on each
panel's border and its outline ({cmd:lcolor()}, {cmd:lwidth()},
{cmd:lpattern()}, {cmd:lstyle()}) once around the array, as in
{cmd:twoway}.  Their {cmd:margin()} insets the array once, as
{cmd:twoway} does: {cmd:plotregion(margin())} by the margin
({cmd:large}, 8 units), {cmd:graphregion(margin())} by the margin less the
scheme's graph margin ({cmd:large} 4.5 units, {cmd:l+5} 5 on the left); a
graph margin smaller than the scheme's, which {cmd:twoway} draws as a
larger array, insets nothing, a dashboard cell having no room to give.
A unit is 1% of the graph's smaller side, by the graph's
{cmd:xsize()}/{cmd:ysize()} or the scheme's size, so the inset follows a
resize of the page.  {cmd:subtitleformat()} writes an
unlabelled panel value in its numeric format ({cmd:var}: the variable's
own), and is ignored, as in {cmd:twoway}, when it is not a numeric format.
The graph's own {cmd:subtitle(, fcolor() lcolor() nobox)} restyle every
panel label's box, and its {cmd:position()} and {cmd:ring()} place every
label as {cmd:twoway} does: above the plot region at 12, 11 and 1 o'clock,
below it at 6, 7 and 5, at its bottom corners at 9 and 3 (below the
region, where {cmd:twoway} draws a narrow box beside it), and, with
{cmd:ring(0)}, inside the region, which takes the label box's fill, at its
bottom; {cmd:by()}'s {cmd:subtitle()} is the overall subtitle.
Each panel's plot-region margin is {cmd:twoway}'s, times the panels' size
multiplier and {cmd:iscale()}.  A one-panel {cmd:by()} whose value label is
empty draws no label box, as {cmd:twoway}, and the Graphs-by note.
{cmd:style(econ)}, {cmd:style(stata7)} and {cmd:style(rescale)} are drawn
as the {cmd:by()} words and graph options their bygraphstyle files give,
which {cmd:twoway} draws line for line alike (econ fills the panels
{cmd:edkbg}; stata7 labels each panel's axes at two values with minor
ticks, its labels unboxed at 11 o'clock; rescale gives each panel its own
axes and scales with three labels, its label boxes outlined in the
foreground line); econ's {cmd:subtitle(, margin(small))} label box and
stata7's major-length minor ticks are drawn too.  {cmd:style(combine)}
draws its words -- separate scales, each panel's own axes and titles,
unboxed labels -- but {cmd:twoway} lays its panels out as
{cmd:graph combine} does, the array 2.2 units in from the graph's edge and
each panel in a graph region of its own (measured: 600 lines of the
exported SVG differ from any {cmd:by()} spelling), which {cmd:dash}'s grid
of panels does not; that is named once.  Any other sub-option of
Stata's {cmd:by()} -- for example {cmd:bgcolor()} -- is accepted, named in
a warning, and ignored.
{cmd:by()} combines with {cmd:link()}: a faceted graph inside a link group
draws its panels as views over the group's one shared data source, so a
box-select in any panel highlights the matching observations in every other
panel and every other linked graph -- in the markers of {cmd:scatter},
{cmd:connected} and {cmd:dot} layers, which draw from that source.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, by(foreign)}{p_end}


{marker marker_labels}
{title:Marker Label Options}

{pstd}
Marker labels are drawn on the plot types {cmd:twoway} draws them on, at
the places {cmd:twoway} draws them (measured against {cmd:twoway}'s own
pictures); see {it:Where labels are drawn} below.  These options apply to
the per-plot specification (not to {cmd:dash build} options).

{synoptset 28}{...}
{synopt:{cmdab:ml:abel(}{it:varname}{cmd:)}}label each observation with
    the value of {it:varname}, on the plot types listed below.  With
    several y variables, each takes the next name; an element may be a
    varlist pattern ({cmd:t*}, {cmd:make-foreign}): its variables label
    the following y's, and names past the last y are dropped, as in
    {cmd:twoway}{p_end}
{synopt:{cmdab:mlabc:olor(}{it:color}{cmd:)}}color of the label text;
    by default the scheme's marker-label colour -- {cmd:color p}{it:#}{cmd:label},
    else {cmd:color plabel}, else the plot's own colour, with its opacity,
    as {cmd:twoway} draws it; {cmd:mcolor()} and {cmd:color label} do not
    change it{p_end}
{synopt:{cmdab:mlabs:ize(}{it:size}{cmd:)}}a text size in Stata's units:
    a {cmd:gsize} keyword ({cmd:small}, {cmd:medium}, {cmd:large}), a
    number, a number with a unit or a {cmd:*}{it:#} multiplier; by default
    the scheme's {cmd:gsize p}{it:#}{cmd:label}, else {cmd:gsize plabel}
    ({cmd:small} in every shipped scheme), and {cmd:*}{it:#} multiplies
    that size{p_end}
{synopt:{cmdab:mlabp:osition(}{it:#}{cmd:)}}clock position of the label
    around the point, a whole number from 0 to 12, placed as {cmd:twoway}
    places it: 3 = right (the default; on {cmd:bar} 12, as {cmd:twoway}'s
    labelstyle {cmd:p#bar} puts it), 12 = above, 6 = below, 9 = left,
    the hours between at the corners, and 0 centred on the point.  Anything
    else -- {cmd:13}, {cmd:2.5}, {cmd:03} or a name -- is reported and the
    label drawn at 12, where {cmd:twoway}, noting it, draws it{p_end}
{synopt:{cmdab:mlabv:position(}{it:varname}{cmd:)}}the clock position of
    each observation's label, read row by row: a whole number from 0 to 12
    is that position; a missing value, and every row of a string variable,
    takes {cmd:mlabposition()} (3 by default), without a note; any other
    number is drawn at 12 and the values are reported once, as {cmd:twoway}
    notes them.  One variable serves every {it:y} of the layer, and
    {cmd:mlabgap()} moves each label along its own row's direction{p_end}
{synopt:{cmdab:mlabt:extstyle(}{it:textstyle}{cmd:)}}one of Stata's text
    box styles -- {cmd:heading}, {cmd:subheading}, {cmd:body},
    {cmd:small_body}, {cmd:label}, {cmd:tick_label}, {cmd:p1} to
    {cmd:p15}, ... -- in the graph's scheme, as {cmd:twoway} draws it.  A
    style list, one element per {it:y}; see
    {help dash##stylelists:Style lists}.  {cmd:mlabsize()} and
    {cmd:mlabcolor()} override it whatever their order.  An unknown name,
    or a textboxstyle file of your own, is reported and the labels drawn
    in {cmd:body}, as {cmd:twoway} draws them{p_end}
{synopt:{cmdab:mlabg:ap(}{it:size}{cmd:)}}space between the marker's
    edge and the label, in the direction of the clock position: a
    {cmd:gsize} in Stata's units, {cmd:half_tiny} (2 point) by default, as
    in {cmd:twoway}.  It is measured from half the layer's marker size
    ({cmd:msize()} when given), on {cmd:bar}, {cmd:pcarrow} and
    {cmd:pcbarrow} too, where no marker is drawn.  A negative gap moves the
    label toward the point, and at {cmd:mlabposition(0)} the label is
    centred on its point{p_end}
{synopt:{cmdab:mlabang:le(}{it:anglestyle}{cmd:)}}angle of the label text,
    counter-clockwise: one of Stata's anglestyles ({cmd:horizontal},
    {cmd:vertical}, {cmd:rvertical}, {cmd:rhorizontal}, {cmd:forty_five},
    ...) or a number of degrees from -360 to 360.  A number outside that
    range is refused where {cmd:twoway} refuses it -- {cmd:scatter},
    {cmd:connected}, {cmd:bar}, {cmd:dot}, {cmd:dropline}, {cmd:rcapsym},
    {cmd:rconnected}, {cmd:rscatter}, {cmd:pcscatter}, {cmd:pccapsym} and
    {cmd:scatteri}.  On {cmd:pcarrow} and {cmd:pcbarrow} {cmd:twoway}
    prints that the angle is out of range but draws the arrows, without
    their labels; {cmd:dash} reports it and draws the labels horizontal.
    A name that is not an anglestyle is reported and the label drawn
    horizontal, as {cmd:twoway} notes it{p_end}
{synopt:{cmdab:mlabf:ormat(}{it:%fmt}{cmd:)}}display format of numeric
    labels.  Any numeric display format -- {cmd:%f}, {cmd:%g} or {cmd:%e},
    with or without {cmd:c} -- is drawn as Stata's {cmd:display} writes it:
    {cmd:mlabformat(%9.1fc)} labels 4099 as {cmd:4,099.0}.  It changes
    nothing on a string or value-labelled variable, as in {cmd:twoway}.  A
    date or string format, one on a date variable, or text that is no
    format is named in a note and the labels drawn without it{p_end}
{synopt:{opt mlabprefix(string)} {opt mlabsuffix(string)}}text
    written before and after every label, as {cmd:twoway} writes
    {cmd:mlabprefix("[") mlabsuffix("]")} as {cmd:[AMC Concord]}; the
    tooltip keeps the bare text{p_end}
{synoptline}

{pstd}
{ul:Where labels are drawn.}  {cmd:scatter}, {cmd:connected}, {cmd:bar},
{cmd:dot} and {cmd:dropline} label each point.  {cmd:rcapsym},
{cmd:rconnected} and {cmd:rscatter} label both ends of each range, as
{cmd:twoway} does, and an end that is missing is left unlabelled on its
own.  A range plot labelled by one of its own variables,
{cmd:rscatter lo hi weight, mlabel(lo)}, is refused as {cmd:twoway}
refuses it, {cmd:rscatter requires 3 variables: lo hi weight}, r(102).
{cmd:pcscatter}, {cmd:pccapsym}, {cmd:pcarrow} and {cmd:pcbarrow}
label the first point, ({it:y1var}, {it:x1var}) -- the tail of an arrow.
{cmd:headlabel} moves those labels to the second point, the head, on
{cmd:pcarrow}, {cmd:pcbarrow} and {cmd:pcarrowi}, as {cmd:twoway} does; on
{cmd:pcscatter} and {cmd:pccapsym} {cmd:dash} names it in the note and
draws the labels at the first point.  A paired-coordinate observation with a missing
coordinate is not drawn at all, marker or label, where {cmd:twoway}, when
only the second point is missing, still labels the first point (and marks
it, on {cmd:pcscatter} and {cmd:pccapsym}).  {cmd:scatteri} and
{cmd:pcarrowi} take their labels from the command line; see
{help dash##plottypes:Plot types}.

{pstd}
{cmd:line}, {cmd:spike}, {cmd:area}, {cmd:rarea}, {cmd:rbar}, {cmd:rspike},
{cmd:rcap}, {cmd:rline}, {cmd:pcspike}, {cmd:tsline}, {cmd:tsrline}, the
fits and smooths ({cmd:lfit}, {cmd:qfit}, {cmd:fpfit}, {cmd:lowess},
{cmd:lpoly}, {cmd:lfitci}, {cmd:qfitci}, {cmd:fpfitci}, {cmd:lpolyci}),
{cmd:histogram}, {cmd:kdensity} and {cmd:function} draw no marker labels:
{cmd:twoway} accepts {cmd:mlabel()} on them and draws nothing, without a
note, and so does {cmd:dash}.  A variable that does not exist is refused,
r(111), as {cmd:twoway} refuses it, except on {cmd:histogram} and
{cmd:function}, where {cmd:twoway} never reads the option.  On
{cmd:mspline} and {cmd:mband} {cmd:twoway} refuses {cmd:mlabel()} -- "too
many variables specified", r(103) -- and so does {cmd:dash}.

{pstd}
{cmd:mlabvposition()} places the labels of {cmd:scatter}, {cmd:connected},
{cmd:bar}, {cmd:dot}, {cmd:dropline}, {cmd:pcscatter}, {cmd:pccapsym},
{cmd:pcarrow} and {cmd:pcbarrow}.  On {cmd:line}, {cmd:spike},
{cmd:area}, {cmd:pcspike} and {cmd:tsline} it is checked and draws
nothing; {cmd:histogram}, {cmd:function}, {cmd:scatteri}, {cmd:pci} and
{cmd:pcarrowi} never read it.  As in {cmd:twoway}, the variable counts as
one more plotted variable, so the range types, {cmd:tsrline}, the fits,
{cmd:mspline}, {cmd:mband}, the smooths and {cmd:kdensity} refuse it,
r(103), in {cmd:twoway}'s words ("rscatter requires 3 variables: ...",
"too many variables specified: ..."); a second copy is refused r(198),
two names r(103), an expression r(198), and a variable that does not
exist r(111).

{pstd}
{ul:What a label says.}  A string variable is drawn as it is.  A numeric
variable with value labels is labelled with its value labels, whatever the
display format or {cmd:mlabformat()} says, and a value with no label with
its number as {cmd:twoway} writes it ({cmd:2}, {cmd:.5}), not in the
display format.  A date variable is labelled with its dates in its own
display format ({cmd:02jan2001}, {cmd:2001m1}, a custom picture as
written), in both render modes; a value label attached to one is not read, where {cmd:twoway} draws
a labelled value's label and any other value's number.  Any other numeric
variable is labelled with its values in its display format, as Stata's
{cmd:display} writes them (a {cmd:float} 0.1 is {cmd:.1}).  A missing value is drawn as {cmd:.};
{cmd:twoway} draws an extended missing value, {cmd:.a} to {cmd:.z}, as its
value label or its name; so does {cmd:dash}: a {cmd:by(, missing)} panel is
titled by it, a marker label and a tooltip show it, and a dropdown filter
offers each code.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, mlabel(make) mlabcolor(navy) mlabsize(small)}{p_end}


{marker smoother_options}
{title:Statistical Layer Options}

{pstd}
The following plot-level options belong to the statistical layers, and
{cmd:base()} to the bar plots.  Each entry names the plot types that take
it, its default and its bounds -- {cmd:twoway}'s, measured against
{cmd:twoway} itself, and {cmd:dash}'s where they differ.  An option that
changes an estimate is honoured or refused.  {cmd:pwidth()} and {cmd:var()} are
honoured on {cmd:lpolyci}; on {cmd:lpoly}, {cmd:scatter}, {cmd:lfitci},
{cmd:kdensity} and the other types {cmd:twoway} refuses them, r(198),
{cmd:option pwidth() not allowed}, and so does {cmd:dash}.  {cmd:fpfit} and {cmd:fpfitci} take none of the smoothing
options -- see below.

{phang}{ul:Fit options.}  {opt atobs} evaluates {cmd:lfit}, {cmd:qfit},
{cmd:lfitci} and {cmd:qfitci} at the observed x instead of the {cmd:n()}
grid ({cmd:fpfitci} takes it and draws as without it, as {cmd:twoway}
does); with {cmd:range()} it is refused, {cmd:may not combine atobs with range()},
r(198).  {opt nofit} draws the band of {cmd:lfitci}, {cmd:qfitci},
{cmd:fpfitci} and {cmd:lpolyci} alone, keyed alone.  {opt fitplot(plottype)}
draws their line as one of {cmd:scatter}, {cmd:line}, {cmd:connected},
{cmd:area}, {cmd:bar}, {cmd:spike}, {cmd:dropline} or {cmd:dot}, and
{opt ciplot(plottype)} their band as a range type ({cmd:rarea}, {cmd:rbar},
{cmd:rspike}, {cmd:rcap}, {cmd:rcapsym}, {cmd:rscatter}, {cmd:rline},
{cmd:rconnected}) or as one of those eight through the lower limit; a name
{cmd:twoway} does not know prints its two notes and draws the default.
Without {cmd:pstyle()}, the view {cmd:ciplot()} names is drawn in the
{cmd:ci} series style, as {cmd:twoway} draws it: its lines in the band's
outline colour (gs12 under {cmd:s2color}; {cmd:ci_line}, gs8, for
{cmd:line} and {cmd:connected}), its markers in {cmd:ci_symbol} and its
bars and areas in {cmd:ci_area}; {cmd:fitplot()} draws the fit in the
layer's colour.  {cmd:ciplot(dot)} draws the markers without
{cmd:dot}'s rows of dots, as {cmd:twoway} draws it.
{opt smoothplot(plottype)} is taken on {cmd:lpolyci} and, as in
{cmd:twoway}, changes nothing.  {opt estopts(string)}, {opt predopts(string)}
and {opt estcmd(cmd)} are run by Stata when the graph is registered --
{cmd:regress} (or {cmd:fracpoly} with {cmd:estcmd()}) and {cmd:predict},
through {cmd:twoway}'s own fit generator -- so the layer is drawn as
registered and does not refit after a filter move: both the saved page and
{cmd:dash serve} mark it, while a move has removed observations, with the
legend key "(unfiltered)", the caption "Marked layers were computed before
the filter" and a note under the filters (the served page's is worded for
{cmd:dash serve}); the served page does not dim it.  A
{cmd:predopts()} of {cmd:predict}'s observation-level options
({cmd:residuals}, {cmd:cooksd}, ...) is evaluated at the observations and
refused with {cmd:range()}, as {cmd:twoway} refuses it.  Their text may not
hold a semicolon, backtick, dollar sign or line break:
{cmd:option estopts() incorrectly specified}, r(198).

{phang}{ul:Recast.}  {opt recast(plottype)}, and its synonyms
{opt recastas(plottype)} and {opt type(plottype)}, are read as
{cmd:twoway} reads them: {cmd:recast()} and {cmd:recastas()} win over
{cmd:type()} in either order, the rightmost copy wins, and one name
serves every y variable.  A {cmd:scatter},
{cmd:line}, {cmd:connected}, {cmd:area}, {cmd:bar}, {cmd:spike},
{cmd:dropline}, range, {cmd:pc} or time-series layer is drawn as the
type named, as {cmd:twoway} draws it; a range type named as a yx type
draws its first bound, and {cmd:tsline} and {cmd:tsrline} still join in
time order.  The fits and smooths, {cmd:kdensity}, {cmd:function},
{cmd:histogram} and {cmd:scatteri} keep their computed points and draw
them as {cmd:scatter}, {cmd:line}, {cmd:connected}, {cmd:area},
{cmd:bar} (one x unit wide), {cmd:spike}, {cmd:dropline} or {cmd:dot},
keyed as the layer is keyed without it; on the saved page a recast fit
is marked after a filter move, and a recast histogram or density is
recounted as the bars and the curve are (drawn as {cmd:dot}, or a
histogram as a range type, it is
marked).  A
{cmd:histogram} also takes the range types ({cmd:rarea}, {cmd:rbar},
{cmd:rspike}, {cmd:rcap}, {cmd:rcapsym}, {cmd:rscatter}, {cmd:rline},
{cmd:rconnected}), its bins drawn as the range from 0 to each bin's
height at the bin's centre; {cmd:rbar}'s bars are the histogram's own,
{cmd:gap()} and {cmd:baroffset()} honoured, and the other range types
stand at the centres, as {cmd:twoway} draws them.  {cmd:pci} and
{cmd:pcarrowi} take the {cmd:pc} types ({cmd:pcspike}, {cmd:pcarrow},
{cmd:pcbarrow}, {cmd:pcscatter}, {cmd:pccapsym}) and draw their
segments as the type named.  The
spellings are {cmd:twoway}'s, case and all; a name outside the source's
class prints {cmd:twoway}'s two notes and falls back -- a yx type to
{cmd:scatter}, a range type to {cmd:rspike}, a {cmd:pc} type to
{cmd:pcspike}, {cmd:function} to its own line.  On {cmd:dot},
{cmd:recast()} is taken and named in the note: {cmd:twoway} reads it
there and draws the dot graph unchanged.  On {cmd:lfitci}, {cmd:qfitci}, {cmd:lpolyci} and
{cmd:fpfitci} {cmd:recast()} and {cmd:recastas()}, and {cmd:type()}
typed in full, are refused, r(198), as {cmd:twoway} refuses them, and so
is a spelling of {cmd:recast()} shorter than its name; the shorter
spellings {cmd:ty} and {cmd:typ} of {cmd:type()} are taken there and drawn
as {cmd:ciplot()} draws them, as in {cmd:twoway}.

{pstd}
{it:Legend keys and default axis titles.}  Each layer is keyed as
{cmd:twoway} keys it: a data layer by its y variable's label, or its
name when it has none; a range or {cmd:pc} layer by both variables,
{it:label1}{cmd:/}{it:label2}, one label when the two are the same;
{cmd:scatteri} {cmd:y}; {cmd:pci} and {cmd:pcarrowi} {cmd:y/yb};
{cmd:lfit} and {cmd:qfit} {cmd:Fitted values}; {cmd:fpfit}
{cmd:Predicted} {it:yvar}; {cmd:lowess} {cmd:lowess} {it:yvar xvar};
{cmd:lpoly} {cmd:lpoly smooth:} {it:ylabel}; {cmd:mband}
{cmd:Median bands}; {cmd:mspline} {cmd:Median spline}; {cmd:function}
by the name before its {cmd:=}, or {cmd:y}; {cmd:histogram}
{cmd:Density} (or its scale); {cmd:kdensity} {cmd:kdensity} {it:varname}.
A {cmd:ci} fit has two keys, its band {it:#}{cmd:% CI} and then its line.
Each axis is titled by default with the label of the first series
drawn on it when the last series drawn on it has the same label, and
is untitled otherwise, as {cmd:twoway} titles it; a {cmd:ci} fit is
two series, band then line.  The rule holds for each axis on its own,
{cmd:yaxis(2)} and {cmd:xaxis(2)} included, and on every {cmd:by()}
panel.  Keys {cmd:twoway} merges into one and the legend it leaves off
a graph of histograms alone are still drawn by {cmd:dash}.

{synoptset 20}{...}
{synopt:{opt bwidth(#)}}the bandwidth of {cmd:lpoly}, {cmd:lpolyci},
    {cmd:kdensity} and {cmd:lowess}.  On the first three it is the
    half-width of the smoothing kernel, in the units of x, days for a
    {cmd:%td} x and months for a {cmd:%tm} one, as
    {helpb twoway lpoly} defines it; with no {cmd:bwidth()} it is
    computed from the data, by {cmd:twoway}'s own rule on {cmd:kdensity}
    and by the rule of thumb under {it:Default bandwidth} below on
    {cmd:lpoly} and {cmd:lpolyci}.  On {cmd:lowess} it is the fraction of
    the sample in each local regression, default 0.8 (see the note
    below).  A positive number; {cmd:kdensity} also takes
    {cmd:bwidth(0)}, meaning the default, and {cmd:lowess} any number,
    reading one of 0 or less, or of 1 or more, as 0.8, as {cmd:twoway}
    does.
    On {cmd:kdensity}, {opt width(#)} is a synonym, as in {cmd:twoway},
    and the two together are refused, r(198).  {cmd:bw()} and {opt bwi()} ..
    {opt bwidth()} are its spellings on {cmd:lowess}, {cmd:lpoly},
    {cmd:lpolyci} and {cmd:kdensity}, as in {cmd:twoway}; elsewhere
    {cmd:bw()} is refused, as {cmd:twoway} refuses it
    ({cmd:option bw() not allowed}; {opt barwidth()} sets a bar's
    width){p_end}
{synopt:{opt pwidth(#)}}{cmd:lpolyci}: the pilot bandwidth of the
    band's variance estimate, in the units of x; by default 1.5 times the
    rule of thumb under {it:Default bandwidth}, even when {cmd:bwidth()}
    is given, as Stata's {cmd:r(pwidth)}.  A positive number; anything
    else is refused in {cmd:twoway}'s words, r(198).  {cmd:pw()} is its
    shortest spelling ({cmd:p()} is {cmd:twoway}'s own {cmd:p()} option,
    the whole plot's style; see {help dash##namedstyles:Named styles}).
    {cmd:pwidth(+800)} is refused as {cmd:twoway} refuses it,
    {cmd:expression invalid}, r(3000){p_end}
{synopt:{opt var(#)}}{cmd:lpolyci}: a constant residual variance for the
    band, in place of the pilot fit's; the pilot window must still hold
    two observations, as in Stata, or that point has no band.  A positive
    number: zero or less is r(198), and a value that is not one number
    r(7), each in {cmd:twoway}'s words.  {cmd:v()} is its shortest
    spelling{p_end}
{synopt:{opt degree(#)}}{cmd:lpoly} and {cmd:lpolyci}: the degree of the
    local polynomial -- 0, the Nadaraya-Watson kernel estimator (the
    default); 1, local linear; 2, local quadratic; 3, local cubic; up to
    7.  {cmd:twoway} takes any whole number from 0 up; {cmd:dash} refuses
    more than 7, r(198), because Stata's rule-of-thumb constants stop
    there{p_end}
{synopt:{opt kernel(name)}}{cmd:lpoly}, {cmd:lpolyci} and {cmd:kdensity}:
    {cmd:epanechnikov} (the default), {cmd:epan2}, {cmd:biweight},
    {cmd:cosine}, {cmd:gaussian}, {cmd:parzen}, {cmd:rectangle} or
    {cmd:triangle}, in upper or lower case, each down to {cmd:twoway}'s
    own abbreviation: {cmd:ep} (so {cmd:epan} is {cmd:epanechnikov};
    {cmd:epan2} is taken only in full), {cmd:bi}, {cmd:cos}, {cmd:gau},
    {cmd:par}, {cmd:rec} and {cmd:tri}.  Any other word is refused,
    r(198), as {cmd:twoway} refuses it ({cmd:twoway} refuses upper case
    too).  {cmd:twoway}'s older spelling,
    the kernel as an option of its own ({cmd:gaussian}), is read as
    {cmd:kernel()} of that name, as {cmd:twoway} reads it, from the same
    abbreviations ({cmd:gau}, {cmd:ep}, {cmd:epan2} in full ...), on these
    three types alone, in lower case; two of them naming different
    kernels are refused, {cmd:only one kernel may be specified}, and one
    beside {cmd:kernel()},
    {cmd:kernel(): old syntax may not be combined with new syntax}
    ({cmd:option kernel(): ...} on {cmd:kdensity}), {cmd:r(198)}, as in
    {cmd:twoway}{p_end}
{synopt:{opt n(#)}}the number of points a layer is drawn at.
    {cmd:lpoly} and {cmd:lpolyci}: 50 by default, over the observed range
    of x, as in {cmd:twoway} -- never more than the dataset has
    observations ({cmd:n(100)} on 74 observations draws 74), and one for
    each observation, whatever {cmd:n()} says, when the dataset has fewer
    than 50; the count is the whole dataset's, not the plot's sample, so
    an {cmd:if} or a {cmd:by()} panel keeps the 50-point grid.
    {cmd:kdensity}: 300 by default, from the minimum to the maximum of the
    plot's sample, or over {cmd:range()}.  {cmd:lfit}, {cmd:qfit},
    {cmd:lfitci} and {cmd:qfitci}: 100 by default, over the observed range
    of x or over {cmd:range()} ({cmd:twoway}'s {cmd:lfit} draws the same
    straight line at 3).  An x that does not vary is a range of one value:
    {cmd:regress} omits x, so every point is at that x and the mean of
    {it:yvar}, as {cmd:twoway lfit} draws it, and the band of
    {cmd:lfitci} and {cmd:qfitci} is the mean's.  {cmd:function}: 300 by
    default, over {cmd:range()}; one graph's {cmd:function} points must fit
    in one Stata macro, {cmd:c(macrolen)} characters (645,200 by default,
    about 21 a point; {cmd:set maxvar} raises it), or the graph is refused
    with {cmd:r(134)}.  On these types {cmd:dash} takes 1 to 10000 (one
    point draws no line, as in {cmd:twoway});
    {cmd:twoway} takes any whole number from 1 up, with no upper bound
    ({cmd:lpoly} reads 1 as 50).  On {cmd:lfit}, {cmd:qfit},
    {cmd:lfitci} and {cmd:qfitci} both take any whole number from 1 up
    (above 10000 the points are made by {cmd:twoway}'s own generator),
    and one from -1 down to minus the dataset's observations, an empty
    fit drawn with its legend key; 0, or a number below that, is refused,
    r(198), "'{it:#}' invalid observation number", and a number that is
    not whole "option n() not allowed".
    {cmd:mspline}: the number of points
    drawn between each pair of adjacent knots, default 10, 1 to 300, as in
    {cmd:twoway}.  {cmd:twoway}'s {cmd:fpfitci} and {cmd:mband} accept
    {cmd:n()} and draw the same points without it, and so does
    {cmd:dash}; on {cmd:fpfitci} any whole number is taken, and a number
    that is not whole is refused as {cmd:twoway} refuses it{p_end}
{synopt:{opt bands(#)}}{cmd:mspline} and {cmd:mband}: the number of
    equal-width bands the range of x is cut into, 1 to 200, as in
    {cmd:twoway}; {cmd:bands(-1)} is the default, as in {cmd:twoway}.  The default is {cmd:twoway}'s:
    round(min(10 log10 {it:N}, sqrt {it:N})), and at least
    min({it:N}, 2), {it:N} the plot's observations{p_end}
{synopt:{opt range(# #)}}the span of x a layer is drawn over.  On
    {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and {cmd:qfitci} the fitted line
    and its band are drawn from one number to the other -- beyond the data
    where the span is wider -- instead of over the observed range of x; on
    {cmd:kdensity} the density is estimated over it instead of from the
    minimum to the maximum of the plot's sample; on {cmd:function} it is
    the range of x, default {cmd:range(0 1)}.  Two numbers, in either
    order.  On the fits a missing end ({cmd:.}) is the observed minimum or
    maximum; on {cmd:kdensity} and {cmd:function} a variable may be given
    instead, whose minimum and maximum over the plot's sample are used, as
    in {cmd:twoway}.  {it:Difference from twoway:} that range is read once,
    when the graph is defined, and a filter move on the page does not
    change it.
    {cmd:twoway} refuses {cmd:range()} on {cmd:fpfit}, {cmd:fpfitci},
    {cmd:lpoly}, {cmd:lpolyci}, {cmd:lowess}, {cmd:mspline}, {cmd:mband},
    {cmd:histogram}, {cmd:scatter} and {cmd:line}{p_end}
{synopt:{opt subchar(name)}}{cmd:function} only: the name the expression
    uses for x, {cmd:x} by default, as in {cmd:twoway}: with
    {cmd:subchar(t)}, the expression {cmd:y = t^2} draws {it:t} squared.  A value
    that is not a name is refused, r(198), as {cmd:twoway} refuses it{p_end}
{synopt:{opt base(#)}}{cmd:bar}, {cmd:spike}, {cmd:dropline} and
    {cmd:area}: the value the bars, spikes, drops and area are drawn from;
    any number.  The axis reaches it, but no tick is placed for it, as in
    {cmd:twoway}.  With no {cmd:base()} they are drawn from 0 when the y
    axis's scale holds 0, and otherwise from the end of the scale nearest
    0, so the axis does not reach 0: {cmd:dash bar mpg weight}, like
    {cmd:twoway bar mpg weight}, draws its bars up from 10.  On a log axis
    that is the scale's lower end, and on a date axis 0 is 01jan1960.
    Under {cmd:by()} the panels share one base unless {cmd:yrescale} gives
    each its own scale, and a {cmd:yaxis(2)} layer takes its base from
    that axis.  The base follows the axis when a filter moves.
    On {cmd:dot}, {cmd:base()} widens the y axis to reach it, as in
    {cmd:twoway}, with no tick placed for it, and does not move the
    markers; the rows of dots run over the axis it widens.
    On {cmd:function}, {cmd:base()} is the base of {cmd:droplines()},
    which {cmd:dash} draws (with no {cmd:base()}, the rule above); a value
    that is not a number is refused in {cmd:twoway}'s words,
    {cmd:option base() incorrectly specified, abc is not a number},
    r(4026).  {cmd:twoway} refuses {cmd:base()}
    on {cmd:histogram}, {cmd:kdensity}, {cmd:rbar}, {cmd:rspike},
    {cmd:rarea}, {cmd:scatter}, {cmd:line}, {cmd:connected} and
    {cmd:lfit}{p_end}
{synopt:{opt gap(#)}}{cmd:histogram} only: each bar is {it:#} percent
    narrower than its bin, about the bin's centre; 0 to 100, 100
    excluded ({cmd:option gap() must be between 0 and 100}, r(198)){p_end}
{synopt:{opt baroffset(#)}}{cmd:bar}, {cmd:rbar} and {cmd:histogram}:
    each bar moved {it:#} bar widths, negative to the left, {cmd:rbar}'s
    as {cmd:bar}'s.  {cmd:twoway} also takes it on {cmd:area},
    {cmd:spike}, {cmd:dropline} and {cmd:dot}, where it draws nothing
    different.  Beside {cmd:rbar}'s {cmd:mwidth} each marker-wide bar is
    moved {it:#} of its own widths to the {it:left} on the screen, as
    {cmd:twoway} moves it, whatever the zoom, and turned by
    {cmd:horizontal} {it:#} of its heights down{p_end}
{synopt:{opt dotextend(yes|no)}}{cmd:dot}: {cmd:dash} draws {cmd:dot} as
    {cmd:twoway} does, a row of dots through each observation and then
    its marker; the rows run up and down from the y axis's base (0 when
    the axis's scale holds 0, else the scale's end nearest 0) to both
    ends of the scale, or with {cmd:dotextend(no)} to the observation's
    value, along x under {cmd:horizontal}.  {cmd:no}, {cmd:n},
    {cmd:off} and {cmd:false} (lower case, as {cmd:twoway} reads them) are
    no; anything else is yes.  The rows follow the axis when a filter
    moves, in the saved page and the served app: each kept observation's
    row is drawn again over the axis the kept rows give.  {cmd:twoway}
    also takes it on {cmd:area}, {cmd:bar}, {cmd:spike} and
    {cmd:dropline}, where it draws nothing different, and refuses it
    elsewhere ({cmd:option dotextend() not allowed}, r(198)){p_end}
{synopt:{opt ndots(#)}}{cmd:dot}: the dots over the scale's whole span,
    75 by default; any number, as {cmd:twoway} takes it (the step is the
    span divided by {it:#} - 1, so {cmd:ndots(1)} draws no dots, and a run
    of more than 10,000 steps is not drawn); anything else is
    {cmd:option ndots() incorrectly specified}, r(198).  Above 2,000,000
    dots in one layer {cmd:dash} draws fewer and says how many.  Taken on
    the types {cmd:dotextend()} is{p_end}
{synopt:{opt dstyle(markerstyle)}}{cmd:dot}: the dots' overall style,
    as {cmd:mstyle()} is the marker's; the dots are otherwise in the
    scheme's {cmd:dots} style (a tiny black circle in {cmd:s2color}), and
    no marker, colour or {cmd:pstyle()} option reaches them.
    {cmd:twoway} takes the d-options on every plot type and draws nothing
    with them but on {cmd:dot}{p_end}
{synopt:{opt dsymbol(symbolstyle)}}{cmd:dot}: the dots' symbol, as
    {cmd:msymbol()}{p_end}
{synopt:{opt dcolor(colorstyle)}}{cmd:dot}: the dots' fill and outline
    colour, as {cmd:mcolor()}{p_end}
{synopt:{opt dfcolor(colorstyle)}}{cmd:dot}: the dots' fill colour, as
    {cmd:mfcolor()}{p_end}
{synopt:{opt dsize(markersizestyle)}}{cmd:dot}: the dots' size, as
    {cmd:msize()}; a dot is drawn at least one pixel across{p_end}
{synopt:{opt dlstyle(linestyle)}}{cmd:dot}: the dots' outline style, as
    {cmd:mlstyle()}{p_end}
{synopt:{opt dlcolor(colorstyle)}}{cmd:dot}: the dots' outline colour,
    as {cmd:mlcolor()}{p_end}
{synopt:{opt dlwidth(linewidthstyle)}}{cmd:dot}: the dots' outline
    width, as {cmd:mlwidth()}{p_end}
{synopt:{opt area(#)}}{cmd:kdensity}: every density multiplied by {it:#};
    positive ({cmd:option area() expects a positive number}, r(198)){p_end}
{synopt:{opt boundary}}{cmd:kdensity}: the curve evaluated one bandwidth
    past the data at each end; not with {cmd:range()}
    ({cmd:only one of options range() or boundary is allowed}, r(198)).
    After a filter move both modes draw it one bandwidth past the kept
    rows{p_end}
{synopt:{opt droplines(numlist)}}{cmd:function}: a line from the base to
    the curve at each {it:x}, drawn before the curve in its line style;
    every {it:x} within {cmd:range()}
    ({cmd:some droplines not within range() option}, r(198)){p_end}
{synopt:{opt nodropbase}}{cmd:area}: the area closes along the line from
    its first point to its last instead of dropping to the base; taken on
    every type, drawing nothing different on the others{p_end}
{synopt:{opt discrete}}{cmd:histogram} only: one bar per distinct value;
    see below.  Refused together with {cmd:bin()}, r(198){p_end}
{synopt:{opt stdp}}{cmd:lfitci}, {cmd:qfitci} and {cmd:fpfitci}: the band
    is built on the standard error of the prediction (the default){p_end}
{synopt:{opt stdf}}{cmd:lfitci} and {cmd:qfitci} only: on the standard
    error of the forecast, sqrt(stdp^2 + rmse^2){p_end}
{synopt:{opt stdr}}{cmd:lfitci} and {cmd:qfitci} only: on the standard
    error of the residual, sqrt(rmse^2 - stdp^2), left missing where
    that is negative.  Two of {cmd:stdp}, {cmd:stdf} and {cmd:stdr}
    together are refused, r(198), as {cmd:twoway} refuses them, and so
    are {cmd:stdf} and {cmd:stdr} on {cmd:fpfitci}
    ({cmd:stdf not allowed}){p_end}
{synopt:{opt mean}}{cmd:lowess} only: a running mean rather than a
    running line ({opt m} is its shortest spelling, as in {cmd:twoway}){p_end}
{synopt:{opt noweight}}{cmd:lowess} only: the tricube weights are
    dropped; {opt weight}, the default, changes nothing, and beside
    {opt noweight} is refused ({cmd:option noweight not allowed}), as in
    {cmd:twoway}{p_end}
{synopt:{opt adjust}}{cmd:lowess} only: the smooth is rescaled so that
    its mean equals the mean of {it:yvar} -- over every observation in
    the data, as {cmd:lowess} computes it, whatever the {cmd:if} or the
    {cmd:by()} panel{p_end}
{synopt:{opt logit}}{cmd:lowess} only: the logit of the smooth is
    drawn, for a 0/1 {it:yvar}; applied after {cmd:adjust}.  Spelled
    {cmd:lo}, {cmd:logi} or {cmd:logit}: {cmd:log} is {cmd:twoway}'s
    graph option {cmd:logging}, on {cmd:lowess} too, which draws nothing
    different and is named in the note{p_end}
{synoptline}

{pstd}
{cmd:lpoly} and {cmd:lpolyci} implement kernel-weighted local polynomial
regression -- the same smoother underlying Stata's {helpb twoway lpoly},
with the same default kernel ({cmd:epanechnikov}) and the same
{cmd:degree(0)} default.  At a given {cmd:bwidth()} the curve is Stata's
at every degree from 0 to 3 -- including where a window's powers of x
are nearly collinear, where the fit keeps the intercept and the powers
Stata's {cmd:invsym()} keeps.  A grid point at which fewer than two observations have
positive kernel weight is left missing, as Stata leaves it, and the line
joins the points on either side of it, as {cmd:twoway lpoly} draws it; a
{cmd:bwidth()} too narrow for any window to hold two observations draws
nothing.  The grid is {cmd:n()} points over the observed range, sized as
{cmd:twoway} sizes it (see {cmd:n()} above).  A kernel weight of 1e-14 or
less does not count toward lpoly's two-observation rule, as in Stata, so
{cmd:lpoly mpg weight, kernel(gaussian) bwidth(1)} on the auto data draws
Stata's 3 points.  Where Stata's result is decided by its own round-off
({cmd:lpoly ylin weight, degree(0)} with ylin = 2*weight+1, y = weight at
degree 0 and 1, a variable near 1e-150 at {cmd:degree(2)}, drawn as
Stata's line at y = 0), dash's exact arithmetic differs by at most 1e-14
relative.  As {cmd:twoway} does, {cmd:dash} counts the sample before it
reads the options -- one observation is "insufficient observations",
r(2001), whatever {cmd:pwidth()} says -- and refuses {cmd:bwidth()},
{cmd:degree()}, {cmd:n()}, {cmd:kernel()} and {cmd:pwidth()} in
{cmd:twoway}'s words ({cmd:pwidth(+800)} is "expression invalid",
r(3000)).

{pstd}
{bf:Note on {cmd:bwidth()} for {cmd:lowess}.}  Stata gives the same option
name two different meanings: for {helpb twoway lpoly} it is an absolute
bandwidth in x units, while for {helpb twoway lowess} it is the
{it:fraction} of the sample used in each local regression (default 0.8).
{cmd:dash} follows Stata in both cases, and draws a {cmd:bwidth()} of 0
or less, or of 1 or more, at 0.8, as Stata's {cmd:lowess} does.

{pstd}
{bf:Default bandwidth.}  With no {cmd:bwidth()}, {cmd:lpoly} and
{cmd:lpolyci} use {cmd:lpoly}'s rule of thumb as Stata computes it (see
{it:Methods and formulas} in {helpb lpoly}): a global polynomial of
degree p+3 in powers of x, where p is the degree and an even degree uses
the next odd one, with Stata's handling of nearly collinear powers; the
residual variance as the weighted mean squared residual of that fit; the
squared (p+1)th derivative of the fit integrated over the central 90% of
the range of x; and Stata's constant for the kernel.  At degree 4 and 5
the bandwidth is Stata's to 5e-4; at degree 6 and 7, where that global
polynomial is of degree 9 or 10 in raw powers, Stata's own round-off is
not reproduced and the bandwidth agrees to about 1%
({cmd:lpoly mpg weight, degree(6)}: 386.3 where {cmd:r(bwidth)} is 390.0).
The bandwidth is
computed from the rows each layer draws: each {cmd:by()} panel and each
{cmd:if} or {cmd:in} gets its own, and the served app recomputes it from
the rows kept after every filter move.  As {cmd:twoway} draws them, an x
taking only the values 0 and 1, or a constant x, gives a line at 0, and
too few distinct points draw nothing.  Where y is an exact polynomial of
x, Stata's bandwidth is the round-off of its arithmetic, and three cases
are drawn differently: y exactly linear in x at {cmd:degree(0)}; y equal
to x at {cmd:degree(0)} or {cmd:degree(1)}; and a y as small as 1e-150
times {cmd:mpg} at {cmd:degree(2)}, which {cmd:dash} draws as a line at 0.

{pstd}
{cmd:lowess} is Stata's smoother, not a library's: the sample is sorted
by x with ties kept in dataset order, each observation is fitted by a
weighted running line over the {cmd:bwidth()} fraction of the sample
centred on it by position, with tricube weights on the distance, and no
robustness iterations are run -- the rule in {manhelp lowess R:lowess},
Methods and formulas.  A window whose x values are all equal has no
line, and the running line is missing there, as Stata's is; the line
joins the points on either side.  Fewer than three observations, or an
x that does not vary, draw nothing.  {cmd:mean} fits a running mean
instead, {cmd:noweight} drops the tricube weights, {cmd:adjust}
multiplies the smooth by the mean of {it:yvar} over every observation in
the data divided by the mean of the smooth (a smooth whose mean is zero
has no adjusted value), and {cmd:logit} draws ln({it:s}/(1 - {it:s})),
where a smooth {it:s} below .0001 is first raised to 1/{it:N} and one
above 1 - .0001 lowered to 1 - 1/{it:N}, as Stata's {cmd:lowess} does
-- a missing smooth, as in Stata, becoming 1 - 1/{it:N} -- with
{cmd:adjust} first when both are given.  {cmd:lowess} takes no weights,
in {cmd:twoway} or here.  {cmd:dash} no longer needs statsmodels for it.

{pstd}
{cmd:mspline} is Stata's estimator: the x range is cut into
{cmd:bands()} equal-width bands, the cross-median (the median x and the
median y) of each non-empty band is a knot, and a cubic spline through
the knots is drawn at the knots plus {cmd:n()} equally spaced points
between each adjacent pair -- a natural cubic spline, which reproduces
Stata's plotted points to the precision Stata stores them at; with one
or two knots only the knots are drawn, as in Stata.  An observation on
a band's edge belongs to the band above it.  As in {cmd:twoway}, the
default number of bands counts every observation with y or x, and the
bands cut the range of every observation with an x, the medians taken
over the observations with both.  {cmd:mband} draws the same
cross medians as a line, from two observations up.  A weight on either
is accepted and, as in {cmd:twoway}, changes nothing -- not even a
missing or zero weight drops its observation.

{pstd}
{cmd:fpfit} and {cmd:fpfitci} implement degree-2 fractional polynomial
fitting (Royston & Altman, 1994), selecting the pair of powers from
{c -(}{cmd:-2}, {cmd:-1}, {cmd:-0.5}, {cmd:0}, {cmd:0.5}, {cmd:1},
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
draws nothing, as in Stata.  That band is its only one: {cmd:stdp} is
accepted, and {cmd:stdf} and {cmd:stdr} are refused, r(198), as
{cmd:twoway} refuses them.  On a date-time x, whose offset is large
against its range, Stata's choice between two nearly equal models can
differ from {cmd:dash}'s; the curves then differ by no more than 5e-4 of
their range (measured).

{pstd}
{bf:{cmd:fpfit} does not take {cmd:bwidth()}, {cmd:degree()} or}
{bf:{cmd:kernel()}.}  Stata refuses all three on {cmd:fpfit} and
{cmd:fpfitci} with r(198) -- a fractional polynomial has no bandwidth or
kernel at all, and its degree is spelled {cmd:estopts(degree(#))}, which
{cmd:dash} honours (see {ul:Fit options} above).
{cmd:dash} accepts the three so a pasted command still runs, and reports
that they were ignored.

{pstd}
{cmd:histogram}'s bin count is {cmd:bin()}, or {cmd:bins()}, which is
{cmd:twoway}'s own name for it ({cmd:bin()} is its abbreviation); both
are read, from 1 to 1000 ({cmd:twoway} has no upper bound).  With
{cmd:discrete} it draws one bar per distinct value, of width
{cmd:width()} or, by default, the smallest positive spacing between the
distinct values (1 when there is only one), each bar centred on its
value; {cmd:start()} does not move the bars, as in Stata, and a value
past the last bar's edge (a {cmd:width()} coarser than the data's
spacing) is counted in the last bar, as Stata counts it.
On every {cmd:histogram}, discrete or continuous, each observation is
counted in bar {cmd:floor((v - start)/width)}, a value at or past the
last edge in the last bar and one below a tolerated {cmd:start()} in
the first, exactly as {cmd:twoway__histogram_gen} counts them.
{cmd:discrete} with {cmd:bin()} is refused, r(198), as {cmd:twoway}
refuses it, and so are {cmd:bin()} with {cmd:width()}
({cmd:options bins() and width() may not be combined}) and two of
{cmd:density}, {cmd:fraction}, {cmd:frequency} and {cmd:percent}
({cmd:options density fraction may not be combined}, the words in that
order).  On any {cmd:histogram} a {cmd:start()} above the smallest
value of the plot's sample is refused, r(198), as {cmd:twoway} refuses
it ({cmd:option start() may not be larger than minimum of} ...); a
variable whose values are all equal is one bar, of width 1 from the
value (centred on it with {cmd:discrete}) or of width {cmd:width()}, as
in Stata.  {cmd:kdensity} evaluates on {cmd:n()} points from the minimum
to the maximum of the plot's sample, or over {cmd:range()}, as
{cmd:twoway kdensity} does.

{pstd}
{cmd:fpfitci}, {cmd:lpolyci}, {cmd:lfitci} and {cmd:qfitci} draw a
confidence band at {cmd:level()}, defaulting to the session's
{cmd:c(level)} -- so {cmd:set level 90} is honoured, as {cmd:twoway}
honours it.  On {cmd:lfitci}, {cmd:qfitci} and {cmd:fpfitci},
{cmd:level(}{it:#}{cmd:)} takes any number, as {cmd:twoway} takes it: at
100 or more no band is drawn, at 0 the band has no width, and below 0 it
is drawn inside out, as {cmd:twoway} draws it.  On {cmd:lpolyci} it is {cmd:twoway}'s rule: 10 to 99.99, with at
most two digits after the decimal point as typed, each refused r(198) in
{cmd:twoway}'s words, and a value that is not one number r(7).
{cmd:lfitci} and {cmd:qfitci} build the band on {cmd:stdp}, {cmd:stdf} or
{cmd:stdr}, {it:t} times that standard error with the same {it:t} for all
three; with an {cmd:aweight}, {cmd:stdf} and {cmd:stdr} are refused as
{cmd:twoway} refuses them ({cmd:not possible with weighted data},
r(135)), and with a {cmd:pweight} likewise (r(198)).  An {it:x} with two
values fits the line ({cmd:qfit} and {cmd:qfitci} omit x^2, as
{cmd:regress} does), and three observations draw the quadratic fit with
no band.  {cmd:lpolyci}'s band is {cmd:lpoly}'s analytic band
({helpb lpoly}, Methods and formulas): the smooth plus and minus
invnormal times its standard error, a sandwich variance with a pilot
local fit of degree p+2 at {cmd:pwidth()}, or {cmd:var()}.  At given
bandwidths it is Stata's; at the default bandwidths it is as exact as the
rule of thumb.  A grid point whose pilot window has no residual degrees of
freedom is drawn with zero width; Stata's value there is round-off, often
missing.  The band is drawn where its standard error is defined and joins
across the points where it is not, as {cmd:twoway lpolyci} draws it.  The
saved page keeps the band computed when it was built; the served app
refits it after every filter move.  The
bound of every checked option is listed under
{help dash##validation:Option values}.

{marker ciband}{...}
{pstd}
{bf:The band's look.}  The band is drawn as {cmd:twoway} draws it, in the
scheme's {cmd:ci} style and not in its line's colour: filled in
{cmd:color ci_area} at {cmd:intensity ci_area} and outlined in
{cmd:color ci_arealine} at {cmd:linewidth ci_area} and
{cmd:linepattern ci_area} -- under {cmd:s2color} an opaque gs12 band
outlined in gs12 -- with the fit line over it.  {cmd:pstyle(p}{it:#}{cmd:)},
{it:#} from 1 to 15, draws the band and the line in that plot style --
the band filled in the scheme's {cmd:color p}{it:#}{cmd:shade} at
{cmd:intensity p}{it:#}{cmd:shade} (each down to {cmd:p}{it:#} and
{cmd:p}, as twoway reads them; an intensity above full, such as
{cmd:inten200}, darkens it as twoway does) -- and
{cmd:pstyle(ci2)} the band in the scheme's {cmd:ci2} colours;
{cmd:pstyle(ci)} and {cmd:pstyle(ci2)} draw the line in
{cmd:color ci_line}.  Any other style name is named in a note and drawn
as {cmd:p1}, which is what {cmd:twoway}'s "default attributes" draw.  The
band takes {cmd:twoway}'s fitarea options:{p_end}

{p2colset 9 30 32 2}{...}
{p2col:{cmdab:col:or(}{it:color}{cmd:)}}the band's fill and outline, and
    the line{p_end}
{p2col:{cmdab:ac:olor(}{it:color}{cmd:)}}the band's fill and outline; wins
    over {cmd:color()} and {cmd:lcolor()}{p_end}
{p2col:{cmdab:fc:olor(}{it:color}{cmd:)}}the fill; wins over
    {cmd:acolor()}{p_end}
{p2col:{cmdab:alc:olor(}{it:color}{cmd:)}}the outline; wins over
    {cmd:acolor()}{p_end}
{p2col:{cmdab:lc:olor(}{it:color}{cmd:)}}the outline and the line{p_end}
{p2col:{cmdab:fi:ntensity(}{it:#}{cmd:)}}the fill's intensity, drawn as
    {cmd:twoway} draws it: the colour blended towards white below 100,
    darker above it, and towards black under {cmd:s1rcolor}{p_end}
{p2col:{cmdab:alw:idth(}{it:lw}{cmd:)}}the outline's width; wins over
    {cmd:lwidth()}, which sets the line's too; 0 to 10000, refused
    outside, r(198), as {cmd:twoway} refuses it; a bare number is read as
    {cmd:lwidth()} reads one{p_end}
{p2col:{cmdab:alp:attern(}{it:lp}{cmd:)}}the outline's pattern; wins over
    {cmd:lpattern()}, which sets the line's too{p_end}
{p2colreset}{...}

{pstd}
A colour's {cmd:%}{it:#} is its opacity, and a colour without one keeps
the style's; {cmd:none} draws no fill or no outline.  {cmd:clcolor()},
{cmd:clwidth()} and {cmd:clpattern()} style the line alone.  On the other
plot types {cmd:acolor()}, {cmd:alcolor()}, {cmd:alwidth()} and
{cmd:alpattern()} are named in the note (see
{help dash##unsupported:Unsupported Stata twoway options});
{cmd:pstyle()} is not.  {cmd:astyle()}, {cmd:alstyle()}, {cmd:bstyle()},
{cmd:blstyle()} and {cmd:lstyle()} style the band in {cmd:twoway}'s order
(see {help dash##namedstyles:Named styles}).

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (lpoly mpg weight, bwidth(400)), saving(lp.html)}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (fpfit mpg weight), saving(fp.html)}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (lfitci mpg weight, stdf), saving(lf.html)}{p_end}
{phang2}{cmd:. dash histogram rep78, discrete saving(h.html)}{p_end}


{marker weights}
{title:Weights}

{pstd}
A weight is written inside a plot as {cmd:twoway} writes it --
{cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=}{it:varname}{cmd:]}
or {cmd:[pweight=}{it:varname}{cmd:]} -- and each statistical layer takes
the types {cmd:twoway} lets it take:

{synoptset 32}{...}
{synopt:{cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}}{cmd:aweight},
    {cmd:fweight}, {cmd:pweight}{p_end}
{synopt:{cmd:fpfit}, {cmd:fpfitci}}{cmd:aweight}, {cmd:fweight},
    {cmd:pweight}{p_end}
{synopt:{cmd:lpoly}, {cmd:lpolyci}, {cmd:kdensity}}{cmd:aweight},
    {cmd:fweight}{p_end}
{synopt:{cmd:histogram}}{cmd:fweight}{p_end}
{synopt:{cmd:mspline}, {cmd:mband}}{cmd:aweight}, {cmd:fweight},
    {cmd:pweight} -- accepted and inert, as in {cmd:twoway}{p_end}
{synopt:{cmd:lowess}}none{p_end}
{synoptline}

{pstd}
The meaning is Stata's: an {cmd:aweight} is normalised to sum to
{it:N}; an {cmd:fweight} replicates observations, so {it:N} is the sum of
the weights; a {cmd:pweight} gives the {cmd:aweight} estimates with a
robust standard error for the band.  A weight's values are treated as
{cmd:twoway} treats them, checked over the plot's own sample -- with a
qualifier written after the plot groups part of it, as in
{cmd:(lfit mpg weight [fw=w]) if foreign == 1}, except on
{cmd:kdensity}, which {cmd:twoway} checks over its own {cmd:if} and
{cmd:in} alone: a
non-integer {cmd:fweight} is r(401) on {cmd:lfit}, {cmd:lfitci},
{cmd:lpoly}, {cmd:lpolyci}, {cmd:histogram} and {cmd:kdensity}, a
negative {cmd:fweight} r(402) on the last four, and a negative
{cmd:aweight} r(402) on {cmd:kdensity}, {cmd:lpoly} and {cmd:lpolyci}.
Elsewhere the command is accepted and the layer drawn as {cmd:twoway}
draws it: {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and {cmd:qfitci} leave a
negative weight's observation out; {cmd:qfit}, {cmd:qfitci}, {cmd:fpfit}
and {cmd:fpfitci} draw nothing for a non-integer {cmd:fweight}, and
{cmd:fpfit} and {cmd:fpfitci} nothing for any negative weight, each with
a note.  A zero weight leaves its observation out, as a missing one
does, on every layer that uses its weights -- except on {cmd:mspline} and
{cmd:mband}, as in {cmd:twoway} (see above).  A weight {cmd:twoway}
refuses, {cmd:dash} refuses with the same code and words:
{cmd:[iweight=]} on any plot type ({cmd:iweights not allowed}), any
weight on {cmd:lowess} ({cmd:weights not allowed}), {cmd:[aweight=]} or
{cmd:[pweight=]} on {cmd:histogram}, and {cmd:[pweight=]} on
{cmd:kdensity}, {cmd:lpoly} or {cmd:lpolyci} -- each r(101) -- and any
weight on {cmd:scatteri}, {cmd:pci} or {cmd:pcarrowi}, r(198)
({cmd:weights not allowed}).  The weight is a variable, abbreviated as
{cmd:twoway} abbreviates a variable, or an expression, as in {cmd:twoway}:
{cmd:dash} checks the expression with Stata's own {cmd:generate} when the
graph is registered (an expression Stata refuses is refused with Stata's
code and words, {cmd:nosuch not found}, r(111)) and evaluates it into a
column of its own when the data are exported, over every observation, so
the layer is fitted as {cmd:twoway} fits it; a time-series term such as
{cmd:L.price} is computed as a time-series operator in a plot variable is
(see {it:Time-series operators} above), and needs {cmd:tsset} data:

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash lfit mpg weight [aw=price+1]}{p_end}

{pstd}
An expression holding a backtick, a dollar sign, a double quote, a
semicolon, a tab or a line break never reaches a command line: Stata's
weight syntax refuses most of them as {cmd:twoway} does, and {cmd:dash}
refuses the rest, r(198).

{pstd}
On {cmd:scatter}, {cmd:line} and the other glyph layers, and on
{cmd:mspline} and {cmd:mband}, {cmd:twoway} reads a weight that names one
variable as that variable's name, word by word, so a range of one
variable, {cmd:[aw=price-price]}, is refused ({cmd:- not allowed},
r(101)), and so are {cmd:[aw=price - price]} and {cmd:[aw=(price)]}
(r(198)); {cmd:dash} refuses them with the same words and codes, after
the plot's options, as {cmd:twoway} does.  Any other expression,
{cmd:[aw=price+1]} or {cmd:[aw=((price))]}, is taken.  A weight on
{cmd:mspline} or {cmd:mband} is taken without a word, as in
{cmd:twoway}.

{pstd}
On {cmd:scatter}, {cmd:connected}, {cmd:dot}, {cmd:dropline},
{cmd:rscatter}, {cmd:rcapsym}, {cmd:rconnected}, {cmd:pcscatter},
{cmd:pccapsym}, {cmd:rpcap} and {cmd:rpspike} (the marker at {it:y3}, not
the caps) an {cmd:aweight}, {cmd:fweight} or {cmd:pweight} sizes the
markers as {cmd:twoway} does: the smallest weight draws its marker at 1.5
times the marker's size -- {cmd:msize()} included -- and every other at
1.5*sqrt({it:w}/{it:wmin}) times it, all scaled down together so the
largest is at most the scheme's {cmd:max_wted_symsize} (10) times the
size.  As in {cmd:twoway}, a weight at or below zero anywhere in the plot
scales every marker by 10*sqrt({it:w}/{it:wmax}) instead; a negative
weight's marker is not drawn, a zero or missing weight's is drawn at size
zero; a plot with no weight above zero stops the graph, r(198), without a
word, as {cmd:twoway} stops it; and markers labelled by {cmd:mlabel()},
and the point symbol, keep their size.  On {cmd:line}, {cmd:area},
{cmd:bar}, {cmd:spike}, the range lines, areas, bars and caps, the pc
lines and arrows, and {cmd:function}, {cmd:twoway} accepts a weight and
draws nothing different, and so does {cmd:dash}, saying nothing.  Both
modes rescale the markers to the rows a filter keeps, a plot with its
own {cmd:if} or {cmd:in} and a panel of a linked {cmd:by()} graph each
to its own kept rows.  On a layer
that uses it the weight is exported with the data; on any other layer the
weight variable is not exported.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (lfitci mpg weight [aw=price]), saving(w.html)}{p_end}


{marker region_options}
{title:Region Styling Options}

{pstd}
{cmd:dash} reads {cmd:plotregion()} and {cmd:graphregion()} as
{helpb twoway} reads them, in the saved dashboard and the served app
alike, before and after a filter move.  Each sub-option is read under
every spelling {cmd:twoway} takes, from the underlined minimum to the
full name, in lower case.

{synoptset 35}{...}
{synopt:{cmd:plotregion(color(}{it:color}{cmd:))}}the fill and the
    outline; shortest {cmd:c()}; every sub-option reads the same in
    {cmd:graphregion()}{p_end}
{synopt:{cmd:plotregion(fcolor(}{it:color}{cmd:))}}the fill; shortest
    {cmd:fc()}{p_end}
{synopt:{cmd:plotregion(lcolor(}{it:color}{cmd:))}}the outline's color;
    shortest {cmd:lc()}{p_end}
{synopt:{cmd:plotregion(lwidth(}{it:lw}{cmd:))}}the outline's width, on
    Stata's line-width ladder, {cmd:*}{it:#} multiplying the region's;
    shortest {cmd:lw()}{p_end}
{synopt:{cmd:plotregion(lpattern(}{it:lp}{cmd:))}}the outline's pattern;
    shortest {cmd:lp()}{p_end}
{synopt:{cmd:plotregion(style(}{it:name}{cmd:))}}a named area style as
    the starting point, such as {cmd:none}; shortest {cmd:sty()}{p_end}
{synopt:{cmd:plotregion(lstyle(}{it:name}{cmd:))}}a named line style for
    the outline; shortest {cmd:ls()}{p_end}
{synopt:{cmd:plotregion(margin(}{it:marginstyle}{cmd:))}}the space
    between the plot region's edge and its scale, per side; shortest
    {cmd:m()}{p_end}
{synopt:{cmd:plotregion(ifcolor(}{it:color}{cmd:))}}the inner box's
    fill; with {cmd:icolor()}, {cmd:istyle()}, {cmd:ilcolor()},
    {cmd:ilstyle()}, {cmd:ilwidth()} and {cmd:ilpattern()}, read as their
    outer forms are; shortest {cmd:ifc()}{p_end}
{synopt:{cmd:graphregion(color(}{it:color}{cmd:))}}the graph region's
    fill and outline; the sub-options above, as in {cmd:plotregion()}{p_end}
{synopt:{cmdab:bgc:olor(}{it:color}{cmd:)}}the canvas under the graph
    region{p_end}
{synoptline}

{pstd}
Within one copy the outline is {cmd:color()} over {cmd:lcolor()} over
{cmd:lstyle()}, and the fill {cmd:fcolor()} over {cmd:color()} over
{cmd:style()}, whatever the typed order, as {cmd:twoway} applies them.
Colors take Stata's grammar (see {help dash##colours:Colours}):
{cmd:none} draws nothing and shows what lies beneath,
{it:color}{cmd:%}{it:#} draws at that opacity over it, and an unknown
color is named in a note and drawn black.  {cmd:lstyle(none)} removes
the outline until a color gives it back.  The graph region's outline is
drawn when an outline sub-option is given.  Repeated copies combine as
{cmd:twoway} combines them, each copy editing the last:
{cmd:plotregion(color(red))} {cmd:plotregion(c(blue))} is blue.

{pstd}
{cmd:bgcolor()} is {cmd:twoway}'s canvas under the graph region.  It
shows only where the graph region (or, through it, the plot region) is
{cmd:none} or translucent, so {cmd:bgcolor(red)} alone changes nothing
you can see and {cmd:bgcolor(red) graphregion(color(none))} shows red.
{cmd:bgcolor(none)} is the color {cmd:none}, black.

{pstd}
{cmd:dash} refuses, with {cmd:twoway}'s words and r(198), what
{cmd:twoway} refuses: an unknown or capitalised sub-option, one shorter
than its minimum, one given twice in a copy, and a word after a comma
inside the region; {cmd:graphregion()} is checked before
{cmd:plotregion()}, and both before {cmd:legend()} and the axis options.
{cmd:intensity()}, {cmd:shadestyle()}, {cmd:graphregion(margin())},
{cmd:ifcolor()}, {cmd:icolor()}, {cmd:iintensity()} and
{cmd:ishadestyle()} are drawn as {cmd:twoway} draws them
({cmd:shadestyle(none)} leaves the region unfilled, and
{cmd:intensity(inten50)} mixes the fill halfway to white, as
{cmd:fintensity()} does a bar's); {cmd:marginonly} keeps that copy's
colours, lines and inner box off and draws only its {cmd:margin()}, as
{cmd:twoway} does, while the region's other copies draw as typed.  {cmd:graphregion(margin())} takes the same
{it:marginstyle} forms as {cmd:plotregion(margin())} below, over the
scheme's {cmd:margin graph} ({cmd:medium}), and widens the figure's
border by the change, a percentage of the figure's smaller side, as
{cmd:twoway} draws it at any size: the border follows a resize of the
page.  On a {cmd:by()} graph {cmd:twoway} draws a {cmd:graphregion(margin())}
given outside {cmd:by()} as nothing, and so does {cmd:dash}; given in
{cmd:by()} it insets the whole array (see Faceting with {cmd:by()}).
{cmd:istyle()}, {cmd:ilstyle()},
{cmd:ilcolor()}, {cmd:ilwidth()}, {cmd:ilpattern()}, {cmd:ilalign()}
and {cmd:lalign()} on {cmd:graphregion()}, and {cmd:lalign()},
{cmd:ilalign()}, {cmd:iintensity()} and {cmd:ishadestyle()} on
{cmd:plotregion()}, are accepted and named in a note, once per region:
{it:difference from twoway}, whose graph region has an inner box between
its margin and the plot region that Bokeh does not draw --
{cmd:graphregion(ilcolor(red))} outlines that box in {cmd:twoway} and
changes nothing in {cmd:dash}, and {cmd:graphregion(ifcolor(red))} fills
the box in {cmd:twoway} and the whole border in {cmd:dash}.  A margin
text {cmd:twoway} fails on -- a style name such as {cmd:allsides-ms}, or
a term whose sign is followed by no number, such as {cmd:l+abc} -- fails
here with its return code and words, r(7).

{pstd}
{ul:Plot-region margin.}  {cmd:plotregion(margin())} takes {cmd:twoway}'s
{it:marginstyle}: one of its 28 names ({cmd:zero}, {cmd:small},
{cmd:medium}, {cmd:sides}, {cmd:10-pt}, ...), four numbers for the left,
right, bottom and top, or terms such as {cmd:l+10}, {cmd:b-2} and
{cmd:t=0}, each side a percentage of the graph's smaller side, applied
in order over the scheme's margin and over earlier copies, so
{cmd:margin(zero)} then {cmd:margin(l+10)} leaves 10% on the left and
none elsewhere.  {cmd:margin(zero)} puts the data and ticks on the plot
region's edge.  Under {cmd:by()} the margin shrinks with the panels, as
the default does.  An unknown single name, such as {cmd:l5}, is named in
{cmd:twoway}'s note and drawn as zero; a text with a sign is read word by
word as {cmd:twoway} reads it, so {cmd:L+10} is the unknown size {cmd:L}
(medium, with {cmd:twoway}'s note) on the left and 10 more on the right.
A number too large for Stata, as in {cmd:l+1e400}, makes that side
medium with {cmd:twoway}'s note, the others kept; set alone, as in
{cmd:l=1e400}, it makes the side zero; and a unit after the sign makes
the side's sum points, so {cmd:l+3pt} over the medium margin is 6.5
points, as {cmd:twoway} draws them.  A side is held within
45% of the plot region.  {it:Difference from twoway:} the margin is a
share of the graph's whole width or height, fixed when the page is
built, so a wide margin is a little narrower on the page than in
{cmd:twoway}, whose plot region is narrower than its graph.

{pstd}
{ul:Inner box.}  The {cmd:plotregion()} inner-box options draw one box at
the plot region's scale, inside the margin, over the data and ticks; it
follows the axes after every filter move and under {cmd:by()}.  Without
an inner-box option no box is drawn.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, plotregion(color(ltblue)) graphregion(color(white))}{p_end}

{pstd}
Abbreviations: {cmd:plotr()} for {cmd:plotregion()},
{cmd:graphr()} for {cmd:graphregion()}, as in {cmd:twoway}.


{marker axis_options}
{title:Axis and Display Options}

{pstd}
The following graph-level options control axis titles, custom tick labels,
annotations, reference lines, axis scaling, tooltips and figure
proportions.
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
{synopt:{cmdab:zt:itle(}{it:string}{cmd:)}}title of the colour key; see {cmd:colorvar()}{p_end}
{synopt:{cmdab:zl:abel(}{it:#}[{it:#} ...][{cmd:, format(}{it:%fmt}{cmd:)}]{cmd:)}}colour-key ticks and number format; see {cmd:colorvar()}{p_end}
{synopt:{cmdab:zsc:ale(}{it:range() log reverse}{cmd:)}}colour-bar range, scale and direction; see {cmd:colorvar()}{p_end}
{synopt:{cmdab:xli:ne(}{it:linearg}{cmd:)}}vertical reference lines; see
    {it:Reference lines} below{p_end}
{synopt:{cmdab:yli:ne(}{it:linearg}{cmd:)}}horizontal reference lines{p_end}
{synopt:{cmd:note(}{it:string}{cmd:)}}footnote text below the figure{p_end}
{synopt:{cmdab:cap:tion(}{it:string}{cmd:)}}caption text below the figure{p_end}
{synopt:{cmdab:aspect:ratio(}{it:#}{cmd:)}}HEIGHT divided by WIDTH, as in
    Stata (e.g. {cmd:aspectratio(1)} for a square plot, {cmd:aspectratio(0.5)}
    for one half as tall as it is wide){p_end}
{synopt:{cmdab:leg:end(off)}}hide the legend{p_end}
{synopt:{cmdab:leg:end(on)}}draw a legend on a graph that has fewer than two
    keys, which would otherwise have none{p_end}
{synopt:{cmdab:leg:end(position(}{it:#}{cmd:))}}place legend by Stata clock
    position, outside the plot: 12 is above, 3 right, 6 below, 9 left; a
    corner sits at that end of its side (1 and 11 at the ends of the top,
    2 and 4 of the right, 5 and 7 of the bottom, 8 and 10 of the left);
    {cmd:position(0)} is the centre of the plot region{p_end}
{synopt:{cmdab:leg:end(ring(0))}}keep the legend inside the plot region
    rather than beside it, at {cmd:position()}'s place there or, alone, at
    the scheme's clock (the bottom centre under {cmd:s2color}){p_end}
{synopt:{cmdab:leg:end(cols(}{it:#}{cmd:))}}arrange legend entries in {it:#} columns{p_end}
{synopt:{cmdab:leg:end(rows(}{it:#}{cmd:))}}arrange legend entries in {it:#} rows{p_end}
{synopt:{cmdab:leg:end(holes(}{it:numlist}{cmd:))}}leave a blank key at each
    position listed{p_end}
{synopt:{cmdab:leg:end(colfirst)}}fill the grid column by column{p_end}
{synopt:{cmdab:leg:end(symxsize() symysize() keygap() rowgap())}}the key's
    width and height, the gap between a key and its text, the gap between
    rows{p_end}
{synopt:{cmdab:leg:end(region() nobox bmargin() bplacement())}}the box's
    outline, fill and inner margin; no box; the space around it; its place
    along its side{p_end}
{synopt:{cmdab:leg:end(title() color() textwidth())}}a title above the keys;
    the key text's colour; its least width{p_end}
{synopt:{cmdab:leg:end(order(}{c -(}{it:#}|{cmd:-}{c )-} [{it:"text"} ...] ...{cmd:))}}select
    and order the keys by plot number, retitle one with text after its
    number, or insert a text-only line after {cmd:-}; a key left out is
    dropped and a number given twice draws the key twice{p_end}
{synopt:{cmdab:leg:end(size(}{it:size}{cmd:))}}font size of the legend text{p_end}
{synopt:{cmdab:leg:end(label(}{it:#} {it:"text"}{cmd:))}}override the label for plot {it:#};
    {cmd:label(}{it:#}{cmd:)} with no text blanks it{p_end}
{synopt:{cmdab:leg:end(lastlabel(}{it:#} {it:"text"}{cmd:))}}the last label applied,
    over {cmd:order()} and {cmd:label()}, to the {it:#}th row as drawn{p_end}
{synopt:{cmdab:cleg:end(}{it:suboptions}{cmd:)}}place the colour key:
    {cmd:off}, {cmd:position()}, {cmd:ring()}, {cmd:title()}, {cmd:width()},
    {cmd:height()}; see {help dash##colorvar:Mapping a Variable to Colour}{p_end}
{synopt:{cmdab:pleg:end(}{it:suboptions}{cmd:)}}place the colour keys
    {cmd:coloruseplegend} puts in the plot legend{p_end}
{synopt:{cmdab:pcyc:le(}{it:#}{cmd:)}}plot styles before {cmd:p1}
    recurs{p_end}
{synopt:{cmdab:xsiz:e(}{it:#}{cmd:)}}graph width in inches; see
    {help dash##geometry:Figure proportions}{p_end}
{synopt:{cmdab:ysiz:e(}{it:#}{cmd:)}}graph height in inches{p_end}
{synopt:{cmdab:xtic:k(}{it:#}[{it:#} ...]{cmd:)}}x-axis tick positions
    without labels{p_end}
{synopt:{cmdab:ytic:k(}{it:#}[{it:#} ...]{cmd:)}}y-axis tick positions
    without labels{p_end}
{synopt:{cmdab:hov:er(}{it:varlist}{cmd:)}}{cmd:dash}'s own: add the
    variables' values to the tooltip; see {it:Tooltips} below and
    {help dash##dashonly:dash's own options}.  {cmd:twoway} refuses it{p_end}
{synoptline}

{pstd}
A legend's sub-options are read as sub-options: a word inside a quoted
label, such as {cmd:label(1 "Turned off")}, is text, never {cmd:off}.
A label's text is read as {cmd:twoway} reads a title's: each string is a
line, so {cmd:label(1 "top" "bottom")} is two; a string in compound
quotes keeps the quotes it holds, nested compound quotes included; and
text with no double quote is one line.
Keys are numbered as {cmd:twoway} numbers its plots: a confidence-interval
fit such as {cmd:lfitci} is two, its band {it:n} and its line {it:n}+1,
and one under {cmd:nofit}, which draws its band alone, as {cmd:twoway}
numbers it.
{cmd:label(}{it:#}{cmd:)} names plot {it:#} wherever {cmd:order()} puts it;
text after a number in {cmd:order()} wins over {cmd:label()}; and
{cmd:lastlabel(}{it:#}{cmd:)} is applied last, to the {it:#}th row drawn, a
{cmd:-} row counted, so {cmd:legend(order(2 1) lastlabel(2 "L"))} renames
the first plot's key.
{cmd:twoway} has no {cmd:legend(top)}, {cmd:legend(bottom)},
{cmd:legend(left)} or {cmd:legend(right)} and refuses each
({cmd:option top not allowed}, r(198)); so does {cmd:dash}, naming the
{cmd:position()} that says what was meant: 12, 6, 9 or 3.

{pstd}
The legend is laid out as {cmd:twoway} lays it out.  Its keys are the
scheme's size -- under {cmd:s2color} a line key 13 units long and
{cmd:medsmall} high, its text a {cmd:vsmall} gap after it, the rows a
{cmd:tiny} gap apart, where a unit is 2.88 points.  A marker key takes the
same box, {cmd:symxsize()} by {cmd:symysize()}: the box does not grow with
the marker, and the browser draws a key's marker at 0.4 of the box's
smaller side, where {cmd:twoway} draws it at the marker's own size and
its key only as wide as the marker.  {cmd:symxsize()}, {cmd:symysize()},
{cmd:keygap()} and {cmd:rowgap()} change them, {cmd:forcesize} draws the
same box, and an unknown size is
{cmd:twoway}'s {cmd:medium}, with a note.  The keys fill a grid of
{it:n} keys, {cmd:holes()} counted: {cmd:rows(}{it:r}{cmd:)} makes
1 + int(({it:n}-1)/{it:r}) columns, {cmd:cols()} the columns given, and
neither the scheme's columns, whatever the position (two under
{cmd:s2color}, so {cmd:legend(pos(3))} is two keys side by side); the
keys fill it row by row, or column by column with {cmd:colfirst}.
{cmd:holes(2)} leaves the second place blank and a hole past the last
key is ignored.
{cmd:region(lcolor() fcolor() lwidth() lpattern() margin())} draws the box, {cmd:nobox} removes it, {cmd:bmargin()} is the
space around it, {cmd:bplacement()} its place along its side,
{cmd:color()} the key text's colour, {cmd:textwidth()} its least width
and {cmd:title()} a line above the keys, with the legend's own
{cmd:subtitle()} a line under it; {cmd:colgap()} is the gap between keys
in one row, as {cmd:twoway} draws it, and {cmd:rowgap()} the gap between
rows (a legend of several rows and columns has one gap, the row gap);
{cmd:span} places a legend beside the plot along its side on the whole
graph instead of the plot region, as {cmd:twoway} draws it -- at 6 or 12
o'clock centred on the graph region's width, at 3 or 9 on its height,
at a corner clock against the graph region's edge (the graph's margin
in, {cmd:graphregion(margin())} included) by the gap it keeps from the
plot region without {cmd:span} -- in the saved page and the served app
and after a resize; {cmd:nospan} undoes the scheme's
{cmd:yesno legend_span} ({cmd:span} beside {cmd:nospan} spans, in either
order, as in {cmd:twoway}), and a legend inside the plot is placed as
without it, as is a {cmd:by()} graph's under the scheme's
{cmd:legend_span}; {cmd:by(}...{cmd:, legend(span))} places {cmd:by()}'s
legend on the whole {cmd:by()} graph the same way.  {cmd:bexpand} and its
{cmd:no} form are taken.  {cmd:textfirst}, {cmd:stacked},
{cmd:symplacement()} and the legend's own {cmd:note()} and
{cmd:caption()} are named in the note: a {cmd:dash} legend draws each key
and then its text in one row, centred in the key's height, with nothing
under the keys, so {cmd:legend(textfirst)}, which {cmd:twoway} draws text
then key, is drawn key then text; {cmd:legend(stacked)}, which
{cmd:twoway} draws with the text under its symbol, and
{cmd:legend(symplacement(n))}, which raises the symbol 28 of the graph's
1,440 SVG units in its key, are drawn as the default; and the legend's
{cmd:note()} and {cmd:caption()}, which {cmd:twoway} writes under the
keys inside the box, are not drawn.

{pstd}
{ul:Axis labels.}  {cmd:xlabel()} and {cmd:ylabel()} take Stata's own
vocabulary, not just a list of numbers:

{synoptset 24}{...}
{synopt:{it:numlist}}explicit tick positions, e.g. {cmd:xlabel(1000 2000 3000)}{p_end}
{synopt:{cmd:#}{it:N}}about {it:N} ticks, placed as {cmd:twoway} places them; see below{p_end}
{synopt:{it:a}{cmd:(}{it:b}{cmd:)}{it:c}}from {it:a} to {it:c} in steps of {it:b}; also {it:a}{cmd:[}{it:b}{cmd:]}{it:c}{p_end}
{synopt:{it:a}{cmd:/}{it:b}}{it:a} to {it:b} in steps of 1 (or -1){p_end}
{synopt:{it:x y} {cmd:to} {it:z}}from {it:x} to {it:z} in steps of {it:y}-{it:x}; also {it:x y}{cmd::}{it:z}{p_end}
{synopt:{it:#} {cmd:"}{it:text}{cmd:"}}label the value before it with {it:text}; a second string is a second line, and a compound-quoted string keeps its quotes{p_end}
{synopt:{cmd:#}{it:N} {it:numlist}}a rule may precede a (labelled) list: both are drawn{p_end}
{synopt:{cmd:minmax}}label only the smallest and largest values{p_end}
{synopt:{cmd:none}}draw no tick labels{p_end}
{synoptline}

{pstd}
The forms mix freely ({cmd:xlabel(1 2 3/5 8(2)12)}).  {cmd:dash} expands
the list with Stata's own {cmd:numlist} before the dashboard is drawn, and
the renderer reads the same grammar for a spec written by hand; a single
quote is a character, not a string delimiter, and a word that is no value,
form, rule or label is named in the note.  More than 2,000 ticks in any
form keep the axis's default ticks, with a note.  Each value is the one
{cmd:numlist} makes, so a rule that crosses zero, such as
{cmd:ylabel(-.3(.1).3)}, labels its middle tick 0.

{pstd}
A default axis, or one labelled {cmd:#}{it:N}, is ticked where Stata's own {cmd:_natscale} and {cmd:_tsnatscale} tick it, asked of Stata over the range each layer draws when {cmd:dash} builds the page; after a filter move the saved page and the served app place {cmd:twoway}'s rule with a fitted model that agrees with Stata on 58-98% of ranges (measured), and a move back to all the data restores Stata's ticks. {cmd:xtick(#}{it:N}{cmd:)} and {cmd:xlabel(minmax)} follow a move the same way. As in {cmd:twoway}, the rows a layer draws include what it evaluates where it draws no point: a {cmd:lowess}, {cmd:qfit}, {cmd:fpfit}, {cmd:lpoly} or {cmd:lpolyci} whose smooth is missing (one or two observations, or a bandwidth that leaves the grid missing) still spans its observations' x on the x axis, and a {cmd:histogram} of no observations runs its y axis from -1 to 1; the other axis is left empty.  A layer with {cmd:range()}, {cmd:recast()} or a date variable spans only the points it draws.
Every count axis is asked so at build -- a {cmd:by()} panel at its own count, {cmd:xmtick(#}{it:N}{cmd:)} and {cmd:xmlabel(#}{it:N}{cmd:)}, a {cmd:histogram}, {cmd:kdensity} or {cmd:function} axis, a fit's grid and band, an immediate layer's and every colour key; {cmd:dash serve} draws the figures once more inside Stata to ask for them, so the served app opens with the same ticks and colour keys.  At most 256 ranges are asked a build; a page rendered outside Stata, and any range past that bound, use the model. A {cmd:histogram}'s bin axis is ticked over its first and last bin midpoints, as {cmd:twoway} ticks it, and spans the bars' edges: {cmd:histogram mpg} labels 15 20 25 30 35 40. {it:Difference from twoway:} the plot-region margin is a fraction of the frame fixed when the page is built, where {cmd:twoway}'s is an absolute size, so a page resized well beyond its built width places the data up to about 1.3% of the plot width from where {cmd:twoway} would at each end (measured below). On an axis with no rule, {cmd:range()} widens the axis but not its ticks, as in {cmd:twoway}: {cmd:yscale(range(0))} on {cmd:mpg} labels 10 20 30 40 over an axis from 0; with {cmd:#}{it:N}, or in a {cmd:by()} graph, the ticks are placed over the data and the range together.

{pstd}
Any of those may be followed by a comma and the sub-options
{cmd:format(}{it:fmt}{cmd:)}, {cmd:labsize(}{it:size}{cmd:)},
{cmd:angle(}{it:#}{cmd:)}, {cmd:grid} or {cmd:nogrid}, and
{cmd:valuelabel} (the axis variable's value labels at the ticks), and
{cmd:norescale}, under {cmd:twoway}'s spellings in lower case
({cmd:ylabel(, for(%9.1f) labs(large) ang(0) nog)}, {cmd:ylabel(, g)},
{cmd:xlabel(0 1, val)}; {cmd:ylabel(, grid nogrid)} draws the grid, as {cmd:twoway} does).
{cmd:nolabels} and {cmd:labels} hide and show the labels, {cmd:noticks}
and {cmd:ticks} the ticks (the positive word wins within one option),
{cmd:labcolor(}{it:colorstyle}{cmd:)} colours the labels ({cmd:%}{it:#}
sets their opacity), {cmd:tlength(}{it:size}{cmd:)} sets the tick length
in Stata's size units ({cmd:*}{it:#} multiplies the scheme's) and
{cmd:tposition(outside}|{cmd:inside}|{cmd:crossing)} the side, each word
from its first letter.  {cmd:angle()} takes a number from -360 to 360,
every anglestyle name ({cmd:horizontal}, {cmd:vertical}, {cmd:forty_five},
{cmd:rvertical} ...) and {cmd:twoway}'s {cmd:h}, {cmd:v}, {cmd:rh} and
{cmd:rv}; another name ({cmd:Vertical}, {cmd:stacked}) gets a note and
level labels, as in {cmd:twoway}, and a number outside -360 to 360 is
refused, {cmd:r(198)}, with {cmd:twoway}'s
{cmd:textangle must be between -360.000 and 360.000}.
{cmd:xtick()} and {cmd:ytick()} take their own {cmd:noticks},
{cmd:tlength()} and {cmd:tposition()}; the label option's tick look never
reaches their positions.
{cmd:labgap()}, {cmd:labjustification()}, {cmd:labalignment()},
{cmd:alternate}, {cmd:altgap()}, {cmd:tlwidth()}, {cmd:tlcolor()},
{cmd:glwidth()}, {cmd:glcolor()}, {cmd:glpattern()}, {cmd:nogmin} and
{cmd:nogmax} are drawn as {cmd:twoway} draws them ({cmd:xtick()} and
{cmd:ytick()} take {cmd:tlwidth()} and {cmd:tlcolor()} for their own
ticks); {cmd:labgap()} moves the labels by its size less the default
{cmd:half_tiny}; {cmd:alternate} staggers the labels on two rows, the
first label on the row nearest the axis and the second row one label
height further out plus {cmd:altgap()}, the axis title outside both;
{cmd:glcolor()} styles a grid that is drawn and does not turn one on;
{cmd:nogmin} drops the gridline at the lowest major tick and {cmd:nogmax}
the one at the highest, every gridline when the labels are a typed list,
as in {cmd:twoway}.  {cmd:tlpattern()}, {cmd:gmin}, {cmd:gmax},
{cmd:gextend} and {cmd:custom} are accepted and change nothing, as in
{cmd:twoway}.  {it:Difference from twoway:} {cmd:nogextend}, which stops
the gridlines at the scale's ends, is named in a note (a Bokeh gridline
spans the plot), and so are {cmd:labstyle()}, {cmd:tstyle()},
{cmd:gstyle()}, {cmd:tlstyle()} and {cmd:glstyle()}, which name Stata
style files {cmd:dash} does not read.  {cmd:alternate} draws on every
axis, {cmd:axis(2)} to {cmd:axis(9)} included, the lowest label on the row
nearest the plot, as {cmd:twoway} draws it.  {cmd:##}{it:#} on a label or tick
option is for minor ticks only: {cmd:twoway} notes
{cmd:##5 ignored, only allowed for minor ticks}, and so does {cmd:dash}; alone it draws what
{cmd:none} draws on a label option and nothing on a tick option.
{cmd:minmax} labels the least and greatest value of every layer on the
axis.  The label forms {cmd:twoway} refuses -- a label with no value
before it ({cmd:ylabel("a")}, {cmd:ylabel(1 "a" "b")}), a second rule
({cmd:ylabel(#3 #4)}) and an unfinished rule ({cmd:ylabel(1(1))}) -- are
refused, {cmd:r(198)}, in its words ({cmd:invalid label specifier, : #4:}).
{cmd:add} adds the listed values to the axis's default ticks, dates
included ({cmd:ylabel(25, add)} draws 10 20 25 30 40 on {cmd:mpg}), in
both modes and after every filter move; after a rule
({cmd:ylabel(15(10)35, add)}, {cmd:#}{it:#}, {cmd:minmax}, {cmd:none}) it
has no effect, and repeated copies merge as {cmd:twoway}'s do
({cmd:ylabel(25, add) ylabel(35, add)} keeps both and the default ticks).
Without {cmd:angle()} the labels take the scheme's
{cmd:anglestyle horizontal_tick} and {cmd:anglestyle vertical_tick}: the y labels are
vertical under {cmd:s2color}, {cmd:s2mono}, {cmd:s2gcolor}, {cmd:s1color},
{cmd:s1mono}, {cmd:s1rcolor}, {cmd:sj}, {cmd:s2manual}, {cmd:s1manual},
{cmd:s2gmanual} and {cmd:s2color8}, and {cmd:angle(0)} or
{cmd:angle(horizontal)} keeps them level.  A spelling
{cmd:twoway} refuses is refused, and quoted label text is text, never a
sub-option ({cmd:ylabel(10 "labsize(large)" 20)} labels 10 with that
text).  As in {cmd:twoway}, label and tick positions widen the
axis to include them, unless {cmd:norescale} is given, which draws them
without widening it; {cmd:twoway} drops {cmd:norescale} from a lone
{it:a}{cmd:(}{it:b}{cmd:)}{it:c} rule and widens that axis anyway, and so
does {cmd:dash}.  {cmd:xscale(range(}{it:numlist}{cmd:))} /
{cmd:yscale(range(}{it:numlist}{cmd:))} widen the axis to include every
value listed, in any order; they never narrow it or hide data.  One value
is one value to include ({cmd:yscale(range(0))} reaches 0 and keeps the
data's top), a missing value is ignored, {cmd:r()} is the abbreviation
and {cmd:rev} that of {cmd:reverse}; a value that is not a number is named
and ignored.  {cmd:xscale()} and {cmd:yscale()} also draw {cmd:off} (the
line, ticks, labels and title go; the grid stays), {cmd:noline} and
{cmd:line}, the axis line's {cmd:lcolor()} (which draws the line beside
{cmd:noline}, as in {cmd:twoway}), {cmd:lwidth()} and {cmd:lpattern()},
{cmd:alt} (the axis on the other side) and {cmd:titlegap(}{it:size}{cmd:)};
{cmd:outergap(}{it:size}{cmd:)} widens the border on the axis's side by the
size less {cmd:twoway}'s default 2 points; {cmd:noextend} runs the axis
line from the first tick to the last; {cmd:lstyle(}{it:linestyle}{cmd:)}
takes a line style's colour, width and pattern ({cmd:lcolor()},
{cmd:lwidth()} and {cmd:lpattern()} win); {cmd:extend}, {cmd:fextend} and
{cmd:fill} draw the plain axis, as in {cmd:twoway}; a second
{cmd:yscale(alt)} toggles the axis back, as in {cmd:twoway}.  The default
gap between an axis's labels and its title is the scheme's
{cmd:gsize axis_title_gap} ({cmd:minuscule}, 1 point, under {cmd:s2color});
{cmd:titlegap(*}{it:#}{cmd:)} multiplies it.  {cmd:zlabel()} and
{cmd:zscale()} on a graph with no colour key change nothing and print
nothing, as in {cmd:twoway}.
An {cmd:lwidth()} outside 0 to 10000 is refused, {cmd:r(198)}, with
{cmd:twoway}'s {cmd:gm_linewidth} message, and a word {cmd:twoway} refuses
({cmd:xscale(bogus)}, {cmd:yscale(OFF)}, {cmd:yscale(alt alt)}) is refused
as it refuses it.  Under {cmd:by()}, {cmd:off}, {cmd:nolabels},
{cmd:noticks} and {cmd:titlegap()} are drawn as if absent, with no note, as
{cmd:twoway} draws them; the rest of the look is drawn on every panel.
The axis then runs, as {cmd:twoway}'s scale does, over the
hull of every layer it draws (fits, confidence bands, {cmd:scatteri} and
{cmd:function} included; reference lines, text, marker labels and the default
base of a {cmd:bar}, {cmd:area}, {cmd:spike} or {cmd:dropline} not), its
ticks, label and tick positions and {cmd:range()} values, plus
{cmd:twoway}'s plot-region margin: 2.2% of the graph's smaller side at each
end (0.6% under {cmd:economist}; a {cmd:by()} panel's scaled as {cmd:twoway}
scales it), in log units on a log axis.  The margin is fixed when the page
is built, so a page drawn wider or narrower than it was built places it up
to about 1.3% of the plot width from {cmd:twoway}'s at each end (measured,
{cmd:scatter mpg weight, ysize(4)}: 1.87% of the width a side at
{cmd:xsize(5.5)}, 2.74% at 2 to 4 inches, 0.86% at 11, 0.58% at 16).  After a filter move a default or {cmd:#}{it:N} axis, a second
axis included, is ticked and spanned again over the rows kept, in the saved
page and the served app alike, and an axis with explicit positions keeps them
and spans its data again; {cmd:xtick(#}{it:N}{cmd:)}/{cmd:ytick(#}{it:N}{cmd:)}
marks and {cmd:minmax} positions (labels and ticks) are placed again over the
rows kept, a {cmd:by()} graph's shared axis once over every panel.  On the saved page a fit,
histogram or grid that
the page does not recompute after a move, marked "(unfiltered)", stays inside
the axis as drawn.

{pstd}
{cmd:#}{it:N} puts the ticks where {cmd:twoway} does: at 1, 2 or 5 times a
power of ten, chosen over the smallest and largest values the axis's layers
draw, and the axis spans its outermost ticks; so {cmd:ylabel(#5)} on
{cmd:auto}'s {cmd:mpg} labels 10 20 30 40.  {cmd:#1} labels the smallest and
largest values.  {cmd:twoway}'s rule is compiled into Stata, so {cmd:dash}
asks Stata for it when the page is built, and after a filter move follows a
model fitted to Stata's answers that agrees with 261 of 264 axes
{cmd:twoway} drew and with 98% of random ranges, and where it differs it
draws a tick more or fewer at an end.  {cmd:xtick(#}{it:N}{cmd:)} and
{cmd:ylabel(#}{it:N}{cmd:, axis(2))} use the same rule.  On a log axis the rule is
the same, over the data's own values, and a tick at or below zero, which a
log axis cannot draw, is left out: {cmd:yscale(log) ylabel(#5)} on
{cmd:price} labels 5,000 10,000 15,000.  A {cmd:%tc} axis takes the same
rule over Stata's milliseconds.  A {cmd:%td}, {cmd:%tw}, {cmd:%tm},
{cmd:%tq}, {cmd:%th} or {cmd:%ty} axis is ticked on calendar boundaries
(days, weeks, the first days of months, quarters and years) by
{cmd:twoway}'s time-series rule, also compiled; {cmd:dash} asks Stata for it
when the page is built and, after a filter move, follows a model of it
fitted to 12,000 of Stata's answers, which agrees exactly with 98% of
{cmd:%ty} ranges and with 58% to 66% of the others, and where it differs
it picks another calendar step or end tick.  A {cmd:by()} graph's panels
are ticked on one scale, over all the panels' data and every layer, fits
included, as {cmd:twoway} ticks them; with {cmd:by(, yrescale)} each panel is
ticked over its own data, as {cmd:twoway} ticks it.

{pstd}
With no {cmd:xlabel()} or {cmd:ylabel()} rule, a numeric, log or {cmd:%tc}
axis, and a second axis with no {cmd:ylabel()} or {cmd:xlabel()} of its own, is ticked
as {cmd:#5} (the scheme's tick count; a {cmd:by()} graph's panels take one
fewer on their first x and y axes, as {cmd:twoway}'s by() styles set them),
with no minor ticks, so
{cmd:scatter mpg weight} labels 10 20 30 40 and 2,000 3,000 4,000 5,000.  A
zoom or pan ticks the visible range by the same rule, and Reset returns to
the current extent.

{pstd}
A {cmd:%td}, {cmd:%tw}, {cmd:%tm}, {cmd:%tq}, {cmd:%th} or {cmd:%ty} axis
with no rule, and a second date axis with none, is ticked as {cmd:#5} (the
scheme's tick count) by {cmd:twoway}'s calendar rule, asked of Stata when
the page is built and modelled after a filter move, with no minor ticks: {cmd:line close date} on {cmd:sp500} labels
01jan2001 01apr2001 01jul2001 01oct2001 01jan2002, as {cmd:twoway} does.
Each axis is asked of Stata over the rows a layer draws, so a series whose
first or last value is missing -- every {cmd:L.} or {cmd:D.} series -- is
ticked as {cmd:twoway} ticks it ({cmd:area d.gnp96 date} labels 1970q1 ...
2000q1).
The model agrees with Stata on about 58-66% of daily to half-yearly ranges
and 98% of yearly ones; otherwise it chooses another calendar step or end
tick.  A date that shares an axis with a plain number is ticked on the
date's calendar in its Stata values, by default and under {cmd:#}{it:N}
alike ({cmd:01jan1960 01jan1970} ... {cmd:01jan2000}).  The axis
re-ticks after a filter move and on zoom, in the saved page and the
served app alike.

{pstd}
A numeric axis's ticks are written in the display format {cmd:twoway}
labels that axis with: the format of the variable its first layer draws
there, so a scatter of {cmd:mpg} on {cmd:weight} in {cmd:auto} labels
{cmd:weight}, whose format is {cmd:%8.0gc}, {cmd:2,000 3,000 4,000 5,000}.
{cmd:set dp comma} is read: every number dash writes uses your decimal mark
({cmd:2.000 3.000} on that axis, {cmd:3,14} for a {cmd:%9.2f} value).
{cmd:%tC} values are converted with Stata's own leap-second table, so
timestamps are exact.
A range plot's axis takes its first y variable's format and a
paired-coordinate plot's its first pair's; a layer's {cmd:xvarformat()}
or {cmd:yvarformat()} replaces its variable's.  {cmd:scatteri},
{cmd:pci}, {cmd:pcarrowi}, {cmd:function}, {cmd:kdensity} and the fits
({cmd:lfit}, {cmd:qfit}, {cmd:lpoly} and their {cmd:ci} forms) are
written in {cmd:%9.0g}, a histogram's heights in {cmd:%6.4g}
({cmd:1.0e-04}), and {cmd:lowess} and {cmd:fpfit} in their x variable's
format and {cmd:%9.0g} on y.  With several layers each axis takes the
first layer drawn on it, and the x axis the first layer of the y axis
whose first layer comes last, as {cmd:twoway} does.  A date axis's ticks
are written in the axis variable's display format: a {cmd:%tm} axis
reads {cmd:2001m1 2001m4}, a {cmd:%td} axis {cmd:02jan2001}, a custom
picture as written.

{pstd}
{ul:Log scales on date axes.}  On an axis drawn in a date format --
{cmd:%tc} and {cmd:%tC} as well as {cmd:%td} to {cmd:%ty} -- the date axis
wins over {cmd:xscale(log)} or {cmd:yscale(log)}: {cmd:dash} draws the
dates on a linear axis, read as the paragraphs above say ({cmd:%tC} with
Stata's leap seconds), and notes "xscale(log) is meaningless for the date
variable '{it:t}'; drawing a date axis instead".  {cmd:twoway} draws a log
scale there, labelled in the date format; measured on twenty monthly
{cmd:%tC} times in 2017-2018, its tick labels sit up to 0.3% of the plot's
width from where a linear axis puts them.

{pstd}
{cmd:format()} writes the axis's stored value in any display format, as
{cmd:twoway} does: on {cmd:sp500}'s {cmd:%td} axis {cmd:format(%9.0fc)}
writes the day numbers {cmd:14,976 15,066}, {cmd:format(%tdDD/NN/CCYY)}
writes {cmd:01/01/2001}, and {cmd:format(%td)} on a numeric axis writes
its numbers as dates.  Ticks beside text labels are written in the same
format.  A format {cmd:twoway} refuses, here or in the colour key's
{cmd:zlabel()}, is refused in its words, {cmd:invalid format, bogus},
r(198).  A string, hexadecimal or byte-dump
format ({cmd:%12s}, {cmd:%21x}, {cmd:%16H}), which {cmd:twoway} accepts,
is written in {cmd:%9.0g} with a note, since {cmd:twoway}'s text can
differ.

{phang}{opt xvarformat(fmt)} and {opt yvarformat(fmt)}, inside a plot,
replace that layer's x or y variable's display format for the axis it
labels, as {cmd:twoway} reads them; written after the plot groups' comma
they are refused, {cmd:option xvarformat() not allowed}, r(198).  A name
that is no format, {cmd:xvarformat(bogus)}, draws the axis in
{cmd:%9.0g} with {cmd:twoway}'s line, {cmd:bogus not found}, rc 0.
{cmd:%d}, {cmd:%td}'s old name, is read as {cmd:%td}, with its picture
({cmd:%dCCYY-NN-DD}), in a variable's format and in these options.  A
business-calendar format, {cmd:%tb}{it:cal}[{cmd::}{it:picture}], is
written as {cmd:twoway} writes it: the calendar is read when the graph is
registered (its days, at most 10,000, travel in the dashboard) and each
value is shown as its business day's date ({cmd:%tbu46 5} is
{cmd:08jan2024}), one outside the calendar as the number, on the axis and
in tooltips.

{phang}{opt yvarlabel(strings)} and {opt xvarlabel(string)}, inside a plot,
stand in for the labels of that layer's variables, as {cmd:twoway} reads
them: the axis titles and the legend keys take them.  {cmd:yvarlabel()}
holds one quoted string per y variable, in order -- a range plot's two
boundaries take the first two, a ci fit's band and line the first, as
{cmd:twoway} writes {cmd:Q/95% CI} and {cmd:Q} -- and {cmd:xvarlabel("")}
draws no x title.

{phang}{opt mlalign(alignmentstyle)} is taken as {cmd:twoway} takes it:
a marker's outline is drawn centred on its edge, which is {cmd:twoway}'s
{cmd:center}; {cmd:inside}, {cmd:twoway}'s default, is silent too,
{cmd:outside} is named in a note, and another word is named in
{cmd:twoway}'s words.  {opt mlabstyle(labelstyle)} styles the marker
labels as the scheme's labelstyle does: {cmd:mlabstyle(p2)} draws them in
p2's label colour at 3 o'clock, {cmd:p2bar} at 12; {cmd:mlabcolor()},
{cmd:mlabsize()} and {cmd:mlabposition()} still win.  A name that is no
labelstyle is named as {cmd:twoway} names it and the labels drawn black
at 12 o'clock, as {cmd:twoway} draws them.  {cmd:msangle()} takes an
anglestyle name as well as a number: {cmd:msangle(forty_five)} rotates
the markers 45 degrees.

{phang}{opt lalign(alignmentstyle)}, inside a plot, is taken as
{cmd:twoway} takes it: {cmd:twoway} draws a line the same with
{cmd:center}, {cmd:inside} or {cmd:outside}, and so does {cmd:dash},
silently; another word is named in {cmd:twoway}'s words, {cmd:named style}
... {cmd:not found in class alignstroke}, and the line drawn without it.
As in {cmd:twoway}, {cmd:lalign} may be shortened to as little as
{cmd:la}, so {cmd:lal} is {cmd:lalign}.

{pstd}
On a date axis a number is a date in the variable's own units, as
{cmd:twoway} reads it: days for {cmd:%td}, milliseconds for {cmd:%tc},
weeks, months, quarters or half-years for {cmd:%tw}, {cmd:%tm}, {cmd:%tq}
and {cmd:%th}, and years for {cmd:%ty}.  So on a {cmd:%td} axis
{cmd:xline(14979)} is drawn at 04jan2001, and {cmd:xlabel()},
{cmd:xtick()} and {cmd:xscale(range())} read their numbers the same way,
in both render modes.  A number that is no date Stata shows (outside
01jan0100 to 31dec9999) is named in a note and not drawn.

{pstd}
{ul:Computed layers of a date.}  The 13 computed types -- {cmd:histogram},
{cmd:kdensity}, {cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci},
{cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci}, {cmd:mspline}, {cmd:mband},
{cmd:fpfit} and {cmd:fpfitci} -- compute from a date in its own units, as
{cmd:twoway} does.  {cmd:width()}, {cmd:start()}, {cmd:bin()},
{cmd:bwidth()}, {cmd:range()} and {cmd:n()} read days for {cmd:%td},
milliseconds after 01jan1960 for {cmd:%tc}, and weeks, months, quarters,
half-years or years for the others.  A density is per day (per month for
{cmd:%tm}), so {cmd:dash histogram date, width(7)} draws week-wide bars.
A histogram's or kdensity's variable is on the x axis.  An axis shows
dates whenever every layer's variable on it is a date of one kind, and a
date layer that shares an axis with a plain number is drawn at its Stata
values, as {cmd:twoway} draws it.  A bar or point computed outside
01jan0100 to 31dec9999 is not drawn, and a note says how many.
{it:Difference from twoway:} twoway labels the axis with the variable's numbers (15000, 15100, ...) when the first layer is {cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci}, {cmd:kdensity}, {cmd:lpoly} or {cmd:lpolyci}; dash keeps its date axis there and draws those layers at the dates their values denote.
So {cmd:dash kdensity date} has a date axis where {cmd:twoway kdensity date} shows 15000 to 15400, and a {cmd:range()} that reaches before 01jan0100 loses those points, with a note, where twoway draws them.

{pstd}
{ul:Dates on every axis.}  A date is placed in its variable's own units on every axis, as {cmd:twoway} places it, in the saved page and the served app, before and after any filter move. The bounds of the range plots ({cmd:rarea}, {cmd:rbar}, {cmd:rspike}, {cmd:rcap}, {cmd:rline}, {cmd:rconnected}, {cmd:rcapsym}, {cmd:rscatter}, {cmd:tsrline}) and the coordinates of the paired plots ({cmd:pcspike}, {cmd:pccapsym}, {cmd:pcarrow}, {cmd:pcbarrow}, {cmd:pcscatter}) count toward the axis they are drawn on, so an {cmd:rarea} whose bounds are {cmd:date} and {cmd:d2} has a date y axis. Each axis is decided by its own layers: a {opt yaxis(2)} or {opt xaxis(2)} layer of a plain number leaves the first axis's dates alone, and a second axis whose layers are dates of one kind is a date axis whose {cmd:axis(2)} labels, ticks, lines and {cmd:range()} read dates, as on the first axis. On a date axis the coordinates of {cmd:scatteri}, {cmd:pci} and {cmd:pcarrowi}, the points of {cmd:function} and an explicit {cmd:base()} of {cmd:bar}, {cmd:spike}, {cmd:dropline} and {cmd:area} are dates too: {cmd:scatteri 1300 15400} on a {cmd:%td} axis is drawn at 01mar2002. A date that shares an axis with a plain number is drawn at its Stata values, the axis labelled in the first layer's date format when that layer draws the date itself (a scatter of {cmd:close} against {cmd:date} beside one against {cmd:obs} reads 01jan1960 at 0), and {cmd:xlabel(minmax)} there ticks those values. A literal coordinate, a {cmd:function} point or a {cmd:base()} outside 01jan0100 to 31dec9999 is drawn where its number falls on the date axis, as {cmd:twoway} draws it ({cmd:scatteri 1300 99999999} reaches 1.00e+08), and a tick there is labelled with its number, as {cmd:display} writes it. {it:Difference from twoway:} a value past the dates a browser can draw (years -271821 to 275760) is not drawn, and a note says so; the ticks of an axis that reaches past Stata's dates are {cmd:dash}'s natscale ticks over its numbers (0 2.00e+07 ... 1.00e+08 where {cmd:twoway} draws 2.50e+07 ... 1.00e+08). Where the first layer is {cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} or {cmd:function}, which {cmd:twoway} labels with numbers, {cmd:dash} keeps the date axis, as for the fits above.

{pstd}
{ul:Ticks without labels.}  {cmd:xtick()} and {cmd:ytick()} add ticks
without labels beside whatever labels the axis has, its default ones or
those {cmd:xlabel()} and {cmd:ylabel()} ask for.  They take a numlist or
{it:a}{cmd:(}{it:b}{cmd:)}{it:c}, {cmd:#}{it:N} or {cmd:minmax}, and the
sub-option {cmd:grid}, which draws gridlines at the ticks; another
sub-option is named in a warning.  Bokeh labels one set of ticks per axis,
so these are drawn as its minor ticks, at the major ticks' length, colour
and width, which are the scheme's; Bokeh's
own minor ticks, which Stata does not draw, are not drawn on that axis.
With {cmd:axis(2)} the ticks are on the second axis's scale, and they
widen that axis, as a label does, unless {cmd:norescale} is given; a line,
{cmd:yline(}{it:#}{cmd:, axis(2))}, never widens an axis.

{pstd}
{ul:Minor ticks and labels.}  {cmd:xmtick()} and {cmd:ymtick()} draw minor
ticks, and {cmd:xmlabel()} and {cmd:ymlabel()} minor ticks with a label at
each, as {cmd:twoway} draws them, in the saved page and the served app.
A scheme's {cmd:numticks_g horizontal_minor} {it:N} (and
{cmd:vertical_minor}) draws as {cmd:xmlabel(#}{it:N}{cmd:)} (and
{cmd:ymlabel()}) where no {cmd:xmlabel()} is given, as {cmd:twoway} draws
it; the shipped schemes' 0 draws none.
They take the grammar of {cmd:xtick()}: a numlist or
{it:a}{cmd:(}{it:b}{cmd:)}{it:c}, with quoted text after a value in
{cmd:xmlabel()}, {cmd:#}{it:N}, {cmd:minmax}, and the rule {cmd:##}{it:N},
which only the minor options take: {it:N}-1 ticks between each pair of
major ticks, the step the major rule's divided by {it:N}, continued in
whole steps to the ends of the scale.  {cmd:##}{it:N} follows the major
ticks after a filter move and a zoom; the other positions stay where they
are, and they widen the axis, as {cmd:xtick()}'s do, unless
{cmd:norescale}.  On major ticks that are no rule {cmd:##}{it:N} draws
what {cmd:twoway} draws: nothing on a date axis, whose labels are calendar
dates, and a single tick at 0 on a list of values such as
{cmd:xlabel(1000 2000 4000)}, evenly spaced or not
({cmd:xlabel(1000 2000 3000)}; {cmd:xlabel(1000(1000)3000)} is a rule).
{cmd:##}{it:N} in {cmd:xlabel()} or {cmd:xtick()} is ignored
with {cmd:twoway}'s note, {cmd:##5 ignored, only allowed for minor ticks}.
A minor tick is the scheme's {cmd:gsize minortick} long ({cmd:half_tiny},
half a major tick) in {cmd:color minortick} at {cmd:linewidth minortick};
a minor label is written in {cmd:gsize minortick_label} ({cmd:vsmall}) in
{cmd:color tick_label}, at the scheme's tick-label angle, a
{cmd:gsize tickgap} from its tick, in the axis's format (or the option's
{cmd:format()}, its quoted text, or with {cmd:valuelabel} its value
label; the option's {cmd:format()} also after a filter move).  An
{cmd:angle()} outside -360 to 360 on {cmd:axis(2)}'s minor labels and
ticks is refused, {cmd:r(198)}, as on the first axis.  {cmd:grid} draws the minor grid in the scheme's
{cmd:minor_grid} style.  Bokeh draws one set of minor ticks per axis, so
an axis with both {cmd:xtick()} and {cmd:xmtick()} draws all of them at
the major ticks' length: {cmd:xtick(10 20) xmtick(15)} draws 15 as long
as 10 and 20.  With {cmd:axis(2)} the ticks and labels are on the second
axis, and with {cmd:axis(3)} to
{cmd:axis(9)} on that axis, each label beside its own axis; labels placed
by {cmd:##}{it:N} follow every filter move on every axis, in the saved
page and the served app.  {opt tmtick()} and {opt tmlabel()} are drawn as
{cmd:xmtick()} and {cmd:xmlabel()}, on axis 2 too, their dates read in
the axis's unit.  An axis outside another on its side draws at most twice the
{cmd:##}{it:N} labels it was built with, plus a few, after a move.

{pstd}
{it:Examples:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(#8, grid) ylabel(10(5)40, format(%9.0f))}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(minmax) yscale(range(0 50))}{p_end}

{pstd}
{ul:Secondary axes.}  Write {opt yaxis(2)} on any plot layer to put it on a
right-hand y axis scaled to what the layers on that axis draw, or
{opt xaxis(2)} for a top x axis; the layer's marker labels and arrowheads go
with it, and the left or bottom axis spans only the layers drawn on it.
Both are plot-level options, given inside the layer's parentheses.  Either
takes 1, 2 or both: a layer on {opt yaxis(1 2)} is drawn once and ties the
two axes into one scale, as {cmd:twoway} ties them -- the right-hand axis
reads the left's scale, and every layer on either axis is drawn on it,
through every filter move.  As in {cmd:twoway}, {opt yaxis()} and
{opt xaxis()} take any of 1 to 9 ({cmd:yaxis(10)} is refused with
{cmd:twoway}'s r(125) and line).  With three or more y axes every one is
drawn on the left, axis 1 nearest the plot and the others outward in number
order; with two, the lower-numbered is on the left and the other on the
right ({cmd:yaxis(1)} and {cmd:yaxis(3)}: axis 3 on the right); x axes
alike, below and above -- as {cmd:twoway} places them under {cmd:s2color}.
When the first layer is not on axis 1, the axes are drawn in the order the
layers first use them, as {cmd:twoway} draws them: the first one used on
the left (bottom) and the next on the right (top), each with the options
written for it -- {cmd:(scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(3))}
has axis 2 on the left and axis 3 on the right, and
{cmd:(scatter price weight, yaxis(2)) (scatter mpg weight)} axis 2 on the
left and axis 1 on the right.  With three or more axes of a letter they
are drawn outward in number order whichever layer uses them first
({cmd:(scatter mpg weight, yaxis(2)) (scatter price weight, yaxis(4)) (scatter trunk weight, yaxis(3))}
draws axes 2, 3 and 4 outward on the left), and an added
{cmd:text(..., yaxis(}{it:#}{cmd:))} stays on the axis it names.  Every second axis re-scales over the rows a
filter move keeps, as the first axes do, in the saved page and the served
app, and a sideways ({cmd:horizontal}) layer on {cmd:yaxis(2)} titles its
axes as {cmd:twoway} titles them.
A layer naming several axes ({cmd:yaxis(2 3)}) ties them into one scale
with every layer on any of them, as {cmd:twoway} does, and every layer on
one axis 3 to 9 alone is drawn on one left (bottom) axis.  An axis 3 to
9 whose layers are dates of one kind is a date axis, labelled in its
variable's date format, as axes 1 and 2 are.

{pstd}
As in {cmd:twoway}, the sub-option {cmd:axis(2)} puts {cmd:ytitle()},
{cmd:ylabel()}, {cmd:ytick()}, {cmd:yline()} and {cmd:yscale()} -- and the
x forms -- on the second axis, and {cmd:axis(1)}, or no {cmd:axis()}, on the
first, and {cmd:axis(3)} to {cmd:axis(9)} on that axis, the {it:t}
forms ({cmd:tlabel()} and the rest) included, their dates read in that
axis's unit:
{cmd:ylabel(5000 10000, axis(2))} labels the right-hand axis,
{cmd:yscale(log axis(2))} makes it a log axis, {cmd:yline(5000, axis(2))}
is drawn on its scale and {cmd:ytick(7500, axis(2))} ticks it, in the saved
page and the served app, before and after any filter move.  Each axis keeps
its own copy: {cmd:ylabel(10 20) ylabel(5000 10000, axis(2))} labels both.
{cmd:twoway}'s spellings are read -- its abbreviations ({cmd:yl},
{cmd:ytic}, {cmd:yli}, {cmd:ysc}, {cmd:yt}), its plurals
({cmd:ylabels()}, {cmd:yticks()}, {cmd:ylines()}) and the sub-option's own
minimum, {cmd:ax(2)} -- written in lower case.  The axis number is read as
{cmd:twoway} reads it: a number that is not a whole number within
{cmd:twoway}'s integer range ({cmd:axis(2.5)}, {cmd:axis(a)},
{cmd:axis(1e300)}) means axis 1.  An {cmd:axis()} naming an axis no layer
is drawn on, an {cmd:axis()} given twice, {cmd:AXIS()} in capitals and a
second comma ({cmd:ylabel(5000, angle(0), axis(2))}) are refused, r(198),
with {cmd:twoway}'s message, in the order {cmd:twoway} checks them.
{cmd:ymlabel()} and {cmd:ymtick()} are checked the same way and drawn on
the axis they name.  {cmd:add} on a label routed to the
second axis ({cmd:ylabel(5000, axis(2) add)}) adds to that axis's default
ticks.

{pstd}
When every layer of a graph is on {opt yaxis(2)}, {cmd:dash} draws one y
axis, on the left, as {cmd:twoway} does; the {cmd:axis(2)} forms --
{cmd:ytitle(..., axis(2))}, {cmd:ylabel(..., axis(2))},
{cmd:yscale(..., axis(2))}, {cmd:ytick(..., axis(2))} and
{cmd:yline(..., axis(2))} -- style it, and the first axis's options are refused,
r(198), with {cmd:twoway}'s message ({cmd:ylabels(5000 10000) not allowed,}
{cmd:yaxis1 does not exist}).  When every layer is on {opt xaxis(2)}, the
one x axis is drawn at the bottom, styled the same way by the x forms.

{marker dashonly}{...}
{pstd}
{it:dash's own options.}  {cmd:dash} takes two options {cmd:twoway} does
not have, because they control what only a dashboard does: {opt hover()},
the variables a tooltip shows, and {opt table}, the data table folded
under a graph; {cmd:twoway} refuses both ({cmd:option hover() not allowed}).
The options of {cmd:dash}'s own subcommands ({cmd:dash build},
{cmd:dash serve}, {cmd:dash kpi}) have no {cmd:twoway} counterpart.  Every
other option is spelled as in {cmd:twoway}: a spelling {cmd:dash} once took
in its place, such as {cmd:ytitle2()} or {cmd:malpha()}, is refused as
{cmd:twoway} refuses it, and the refusal's second line names {cmd:twoway}'s
spelling ({cmd:use ytitle(..., axis(2))}).

{marker taxis}{...}
{pstd}
{it:Time-axis options.}  {opt tlabel()} ({cmd:tl}), {opt ttick()}
({cmd:ttic}), {opt tmlabel()} ({cmd:tml}), {opt tmtick()} ({cmd:tmt}),
{opt ttitle()} ({cmd:tt}), {opt tscale()} ({cmd:tsc}) and {opt tline()}
({cmd:tli}) are {cmd:twoway}'s time-axis spellings of {cmd:xlabel()},
{cmd:xtick()}, {cmd:xmlabel()}, {cmd:xmtick()}, {cmd:xtitle()},
{cmd:xscale()} and {cmd:xline()}.  As in {cmd:twoway}, they act on the
first x axis of any twoway graph, not only {cmd:tsline}, and are read
after the x options whatever the order they are typed in: a later copy
replaces or joins the x one as a second x copy would, and lines add up.
A date literal is read in the unit of the x axis's label format, the
format of the first plot's x variable ({cmd:2002m1} is 504 on a
{cmd:%tm} axis, {cmd:15feb2000} 14655 on a {cmd:%td} one), as
{cmd:twoway}'s {cmd:d()}, {cmd:w()}, {cmd:m()}, {cmd:q()} and {cmd:h()}
read it; a number is a number first ({cmd:01012001} is 1012001).  The
axis takes numbers only when its format is {cmd:%tc}, {cmd:%tC},
{cmd:%tb} or numeric, or when the first plot is {cmd:lfit}, {cmd:qfit},
{cmd:lfitci}, {cmd:qfitci}, {cmd:lpoly}, {cmd:lpolyci}, {cmd:kdensity},
{cmd:function}, {cmd:scatteri}, {cmd:pci} or {cmd:pcarrowi}; the
paired-coordinate types read their first x variable, and an operated x
({cmd:L.t}) its variable.  {opt tmlabel()} and {opt tmtick()} are drawn
as {cmd:xmlabel()} and {cmd:xmtick()} are; {cmd:tscale(log)} on a date axis is noted as
{cmd:xscale(log)} is.  What {cmd:twoway} refuses is refused in its words:
a date literal in {cmd:xlabel()}, {cmd:xtick()}, {cmd:xmlabel()},
{cmd:xmtick()} or {cmd:xline()} (r(198)) or in {cmd:xscale(range())}
(r(121)), and likewise in {cmd:ylabel()}, {cmd:ytick()}, {cmd:ymlabel()},
{cmd:ymtick()} or {cmd:yline()} (r(198)) or in {cmd:yscale(range())}
(r(121)), on any {it:y} variable, a date-formatted one too; a literal on an axis that takes numbers only, or one no
date function reads ({cmd:tline(2000m13)}); more than 2,500 lines in a
copy (r(123)); and {cmd:tm()} and {cmd:ts()}, which are no option of
{cmd:twoway}'s (r(198)).  The dates are read when the graph is
registered; if the axis variable's date format changes before
{cmd:dash build}, a note says so and the registered values are drawn.

{pstd}
As with the x options, {cmd:axis(2)} puts a time-axis option on the second
x axis, whose dates are read in that axis's own unit (its first plot's
format); {cmd:twoway}'s plurals ({cmd:tlabels()},
{cmd:tticks()}, {cmd:tlines()}) are read.  An {cmd:axis()} no layer uses is
refused in {cmd:twoway}'s words, the x options' first, then the time
axis's, then the y options' ({cmd:tlabels(2001m1, axis(3)) not allowed,}
{cmd:xaxis3 does not exist}).  A {cmd:format()} decides the unit as
{cmd:twoway}'s tick sets do: {cmd:line y n, xlabel(, format(%tm))}
{cmd:tline(2002m1)} reads a month on an unformatted {cmd:n}; an option's
own {cmd:format()} applies only after its own positions, so
{cmd:tlabel(2001m1, format(%tm))} on {cmd:n} is refused; and lines and
{cmd:range()} take the first {cmd:%t} or {cmd:%d} format among the label,
minor label, tick and minor tick formats.  A left-aligned {cmd:%-tm} axis
reads dates in labels and ticks, but its lines and {cmd:range()} take
numbers only, as in {cmd:twoway}.

{synoptset 38}{...}
{synopt:{cmdab:tl:abel(}{it:rule_or_values}{cmd:)}}{cmd:xlabel()} with date
    literals{p_end}
{synopt:{cmdab:ttic:k(}{it:rule_or_values}{cmd:)}}{cmd:xtick()} with date
    literals{p_end}
{synopt:{cmdab:tml:abel(}{it:rule_or_values}{cmd:)}}{cmd:xmlabel()} with
    date literals{p_end}
{synopt:{cmdab:tmt:ick(}{it:rule_or_values}{cmd:)}}{cmd:xmtick()} with date
    literals{p_end}
{synopt:{cmdab:tt:itle(}{it:tinfo}{cmd:)}}{cmd:xtitle()}{p_end}
{synopt:{cmdab:tsc:ale(}{it:axis_suboptions}{cmd:)}}{cmd:xscale()}, its
    {cmd:range()} read as dates{p_end}
{synopt:{cmdab:tli:ne(}{it:linearg}{cmd:)}}{cmd:xline()} with date
    literals{p_end}
{synoptline}

{pstd}
{it:Reference lines.}  {cmd:xline()} and {cmd:yline()}, on either axis,
take a {it:linearg}, {it:numlist} [{cmd:,} {it:suboptions}],
as {cmd:twoway} does: the positions are expanded by Stata's own
{cmd:numlist} ({cmd:2000(500)3000}, {cmd:2000/2002},
{cmd:2000 2500 to 3500}), each value once within a copy and at most 2,500
in a copy.  Each copy of a repeated option keeps its own style.  The
sub-options are {cmd:lcolor()} ({cmd:lc()}), {cmd:lwidth()} ({cmd:lw()}),
{cmd:lpattern()} ({cmd:lp()}), {cmd:lstyle()} ({cmd:lst()}), which takes
any line style name ({cmd:p1}, {cmd:refline}, {cmd:foreground},
{cmd:grid}, {cmd:none}, ...) with {cmd:lcolor()}, {cmd:lwidth()} and
{cmd:lpattern()} drawn over it, and {cmd:lalign()} ({cmd:la()}), accepted
as {cmd:twoway} accepts it, with no visible change.  What
{cmd:twoway} refuses is refused in its words and order:
{cmd:something required}, {cmd:r(100)}, for an empty list with a comma;
{cmd:option }{it:name}{cmd: not allowed}, {cmd:r(198)}, for an unknown,
short, capitalised or repeated sub-option; and
{cmd:invalid line argument}, {cmd:r(198)}, for positions {cmd:numlist}
refuses.  The lines are drawn above the grid and below the data, and
never widen an axis, as in {cmd:twoway}.  A position outside the axis's
range is drawn by {cmd:twoway} only where it falls on the graph's canvas
-- beside the plot region, in the graph region's margin
({cmd:xline(5100)} on {cmd:scatter mpg weight}) -- and a farther one off
the canvas or at a wrapped coordinate (its {cmd:xline(10000)} appears
near 2,136).  dash draws every line within
the plot region: Bokeh clips the lines it draws in a plot to its frame,
and only a data layer drawn over the markers would paint outside it, so
a line in that margin strip is not seen.  See {cmd:$dash_max_reflines} under
{it:Resource limits}.

{pstd}
{cmd:noextend} ({cmd:noex}), {cmd:extend} ({cmd:ex}) and
{cmd:style(default}|{cmd:extended}|{cmd:unextended)} ({cmd:st()}) are
drawn as {cmd:twoway} reads them: the scheme's
{cmd:yesno xyline_extend_low} and {cmd:yesno xyline_extend_high} (yes in
every shipped scheme) set where a line ends, then {cmd:style()}, then
{cmd:noextend}, then {cmd:extend}, whatever order they are typed in.  An
end that is not extended stops at the axis's scale, inset from the frame
by the plot-region margin (none under {cmd:plotregion(margin(zero))}),
and follows the axis after every filter move; a line the scheme or
{cmd:noextend} stops at the plot-region margin keeps its ends at the
margin through a zoom or a pan, on any axis; another {cmd:style()} name
is drawn as the default with {cmd:twoway}'s note.

{pstd}
{cmd:ytitle(..., axis(2))} and {cmd:xtitle(..., axis(2))} are read the
same way every other text option is: each quoted string is its own line,
{cmd:size()} and {cmd:color()} are applied, and any other sub-option is
named once.  An empty string ({cmd:ytitle("", axis(2))}) removes the title; without one, the
second axis is titled as {cmd:twoway} titles it -- by the rule of the
first axis, over its own layers' series -- in the scheme's axis style, and
sub-options alone style that title; under {cmd:by()} it has no default
title, as in {cmd:twoway}.

{pstd}
{cmd:ylabel(..., axis(2))} and {cmd:xlabel(..., axis(2))} read their rule
and sub-options with the parser {cmd:ylabel()} uses: a numlist, {cmd:#}{it:N},
{it:a}{cmd:(}{it:b}{cmd:)}{it:c}, {cmd:minmax}, {cmd:none}, value-label
pairs, {cmd:format()}, {cmd:labsize()}, {cmd:angle()}, {cmd:grid} (which
draws gridlines at the second axis's ticks) and the label and tick look of
{cmd:ylabel()}, under the same spellings; any other sub-option is named
in a warning.  {cmd:yscale(..., axis(2))} and {cmd:xscale(..., axis(2))} take {cmd:log},
{cmd:reverse} ({cmd:rev}) and {cmd:range(}{it:numlist}{cmd:)} ({cmd:r()}),
which widens the second axis only, as {cmd:yscale(range())} does, and the
look of {cmd:yscale()}, where {cmd:alt} puts the second axis on the first
axis's side, outside it; they name anything else; the second axis's label
positions widen
the second axis unless {cmd:norescale} is given.  With or without them, a
second axis's ticks are written in the format of the first layer on it,
as {cmd:twoway} writes them.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse sp500, clear}{p_end}
{phang2}{cmd:. dash (line close date) (line volume date, yaxis(2)), ytitle(Volume (thousands), axis(2))}{p_end}

{marker graph_text}{...}
{pstd}
{ul:Text in graphs.}  Text {cmd:dash} draws on a graph -- a title,
subtitle, note or caption, an axis title, a tick label, a legend key or
title, a {cmd:by()} panel title, the colour key and a marker label,
typed in an option or taken from a variable label, a value label or a
string variable -- reads Stata's graph-text markup as {cmd:twoway} does
(see {help graph_text}): {cmd:{c -(}bf:}{it:text}{cmd:{c )-}},
{cmd:{c -(}it:}{it:text}{cmd:{c )-}}, {cmd:{c -(}sup:}{it:text}{cmd:{c )-}},
{cmd:{c -(}sub:}{it:text}{cmd:{c )-}}, the font tags
{cmd:{c -(}stSans:}, {cmd:{c -(}stSerif:}, {cmd:{c -(}stMono:},
{cmd:{c -(}stSymbol:} and {cmd:{c -(}fontface "}{it:name}{cmd:":}, each
also as {cmd:{c -(}bf{c )-}}, which holds to the end of the line, the
symbols {cmd:{c -(}&}{it:name}{cmd:{c )-}} ({cmd:{c -(}&alpha{c )-}} is
the Greek letter alpha) and the characters {cmd:{c -(}c }{it:#}{cmd:{c )-}},
{cmd:{c -(}c 0x}{it:#}{cmd:{c )-}} and {cmd:{c -(}c }{it:name}{cmd:{c )-}}.
The characters are drawn in Unicode.  A text drawn on a graph has one
style, one font and one baseline, so markup that covers the whole text
makes it bold, italic or in that font, and a raised or lowered run uses
Unicode's superscript or subscript characters when each of its
characters has one (digits, {cmd:+ - = ( )} and, raised, {cmd:n} and
{cmd:i}).  Markup on part of a text, or a raised run without such
characters, is drawn in the text's own style and on the line, and
{cmd:dash} says so in one note for each graph and kind of text:
{cmd:twoway} draws {cmd:title("a {c -(}bf:b{c )-} c")} with only the b
bold and {cmd:a{c -(}sup:q{c )-}} with the q raised, where a text
{cmd:dash} draws has one style and one baseline and q has no Unicode
superscript.  Tick labels and legend keys take a style only when every
one of them has it.  {cmd:{c -(}stSans:}, {cmd:{c -(}stSerif:} and
{cmd:{c -(}stMono:} draw in the reader's sans-serif, serif and monospace
fonts (Helvetica, Times and Courier where installed), and
{cmd:{c -(}fontface{c )-}} needs that font on the reader's computer.
A {cmd:graph set} font face is read where Stata keeps it and leads the
{c -(}stSans{c )-}, {c -(}stSerif{c )-} and {c -(}stMono{c )-} families.
As in {cmd:twoway}, a text is cut off at {cmd:{c -(}c 0{c )-}}: the rest
of the run it sits in is not drawn, and text after that run's closing
brace, and the text's other lines, are drawn.  The control codes
({cmd:{c -(}c 1{c )-}} to {cmd:{c -(}c 31{c )-}},
{cmd:{c -(}c 127{c )-}}, 129, 141, 143, 144 and 157) are kept as those
characters; the page carries them as escaped text, never as markup or
script.  One small difference is kept: a symbol inside
{cmd:{c -(}stSymbol:} is drawn as itself.

{pstd}
The other SMCL directives are drawn as {cmd:twoway} draws them, which
reads a graph's text as the Results window does on a line of 254
columns: {cmd:{c -(}hline }{it:#}{cmd:{c )-}} is {it:#} hyphens and
{cmd:{c -(}hline{c )-}} hyphens to column 254;
{cmd:{c -(}space }{it:#}{cmd:{c )-}} is {it:#} blanks;
{cmd:{c -(}dup }{it:#}{cmd::}{it:text}{cmd:{c )-}} is the text {it:#}
times, its markup read; {cmd:{c -(}cmd:}{it:text}{cmd:{c )-}} and
{cmd:{c -(}hi:}{it:text}{cmd:{c )-}} are the text in the style around
them; {cmd:{c -(}center:}{it:text}{cmd:{c )-}} centres the text on what
is left of the line and {cmd:{c -(}center }{it:#}{cmd::}{it:text}{cmd:{c )-}}
in {it:#} columns, {cmd:{c -(}rcenter:} likewise with an odd blank on
the left, {cmd:{c -(}right:}{it:text}{cmd:{c )-}} ends the text at column
254 and {cmd:{c -(}col }{it:#}{cmd:{c )-}} moves to column {it:#} (never
back; {cmd:{c -(}col }{it:#}{cmd::}{it:text}{cmd:{c )-}}, which
{cmd:twoway} draws as a repeat of its text (measured:
{cmd:{c -(}col 5:x{c )-}} is xxx), is drawn as typed); the links {cmd:{c -(}browse{c )-}},
{cmd:{c -(}help{c )-}} and {cmd:{c -(}stata{c )-}} are their text after
the colon, or their argument when they have none; and
{cmd:{c -(}ccl }{it:name}{cmd:{c )-}} is {cmd:c(}{it:name}{cmd:)} -- in
a graph option's text or a {cmd:text()} line when the graph is
registered, in a variable or value label when the page is built -- and
{cmd:{c -(}ccl version{c )-}} is 9, the version {cmd:twoway} draws
under.  A
{cmd:$}{it:name} or {cmd:${c -(}}{it:name}{cmd:{c )-}} that reaches
{cmd:dash} in a title, subtitle, note, caption, axis or edge title,
legend or tick label -- written {cmd:\$name} in a do-file -- is the
global's value, as {cmd:twoway} reads the option's whole text again
before its quotes are read (so a global holding a double quote splits
the string, as in {cmd:twoway}, and in {cmd:text()}, {cmd:ttext()} or a
tick label is refused in its words, {cmd:invalid point, }{it:...} or
{cmd:invalid label specifier, :}{it:...}{cmd::}, {cmd:r(198)}) and its
sub-options too; by text only: a
global holding {cmd:`=1+1'} is drawn as written, where {cmd:twoway}
evaluates it, and an option whose globals expand past 4,000 characters
is refused, {it:option}{cmd:(): expanded text is too long},
{cmd:r(198)}.  A count above
255 (above 999 for {cmd:{c -(}dup{c )-}}), which {cmd:twoway} does not
read, and an unknown tag are drawn as typed, as are {cmd:$$} and
{cmd:\(} pairs.  A line longer than 254 characters is drawn as
{cmd:twoway} draws it: only its last piece, up to 252 characters after
{cmd:>}.  The expansions of one line stop at 4,000 characters; the rest
is not drawn, and {cmd:dash} says so in its note.

{pstd}
Around the graphs, a filter's title, a dropdown's options taken from
value labels and a tooltip's row names show the characters, without the
style and font tags.  KPI titles, the dashboard's title and subtitle,
{cmd:tabs()} titles, string values in tooltips and dropdowns, and the
{cmd:csv} download keep the text as it is stored.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, title("{c -(}&alpha{c )-} = R{c -(}sup:2{c )-}") subtitle("{c -(}bf:Fuel economy{c )-}")}{p_end}

{pstd}
{ul:Tooltips.}  Each layer's tooltip names the variables that layer
plots -- its x and y, a range's two ends, a paired-coordinate layer's
x1, y1, x2 and y2 -- so in {cmd:(scatter mpg weight) (scatter price weight)}
a point of the second layer shows {cmd:weight} and {cmd:price}, not
{cmd:mpg}.  Each row is named by the variable's label, or by its name
when it has none.  {cmd:hover(}{it:varlist}{cmd:)} adds the variables' values
to the tooltip of every layer whose marks are observations --
{cmd:scatter}, {cmd:connected}, {cmd:line}, {cmd:tsline}, {cmd:area},
{cmd:dot}, {cmd:dropline}, {cmd:bar}, {cmd:spike}, every range type
({cmd:rarea}, {cmd:rbar}, {cmd:rspike}, {cmd:rcap}, {cmd:rcapsym},
{cmd:rline}, {cmd:tsrline}, {cmd:rconnected}, {cmd:rscatter}, {cmd:rpcap},
{cmd:rpspike}) and every
paired-coordinate type drawn from variables ({cmd:pcspike},
{cmd:pcarrow}, {cmd:pcbarrow}, {cmd:pcscatter}, {cmd:pccapsym}) -- in the
saved dashboard and the served app alike.  {cmd:hover()} given more than
once -- inside a layer's parentheses and again after the comma, or twice
in one option list -- shows every list's variables, in the order written,
each once.  Each point shows the values of
its own observation; both points of an {cmd:rscatter} or a
{cmd:pcscatter} show the same one.  A computed layer's points are not
observations -- {cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci},
{cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci},
{cmd:mband}, {cmd:mspline}, {cmd:kdensity}, {cmd:histogram} and
{cmd:function} -- and an immediate layer's ({cmd:scatteri}, {cmd:pci},
{cmd:pcarrowi}) are typed in the command, so {cmd:hover()} cannot reach
them: their tooltips, where they have one, show only what the layer draws,
x and y, a {cmd:kdensity}'s x and {cmd:Density}, or a histogram's bin and
its height, named as its y axis is titled ({cmd:Density},
{cmd:Frequency}, {cmd:Fraction} or {cmd:Percent}), and {cmd:dash} names each such
layer in a note, once.  A variable's value -- a computed layer's bins and
points too -- is written in its display
format, as Stata's {cmd:display} writes it -- {cmd:4,099} under
{cmd:%8.0gc}, {cmd:12345.67} under {cmd:%10.0g}, a date in its picture,
a {cmd:%tc} or {cmd:%tC} date with its time -- in both render modes.
Every variable {cmd:hover()} names is exported with the data, whether or
not a layer plots it, so its value is in the tooltip of the saved
dashboard and the served app, before and after a filter move; its values
are part of the saved page's source, like the variables the layers draw.
{cmd:dash build} and
{cmd:dash serve} refuse a {cmd:hover()} variable no longer in memory with
r(111), as they refuse a dropped plotted variable.

{marker edge_titles}{...}
{pstd}
{ul:Edge titles.}  {opt t1title()}, {opt t2title()}, {opt b1title()},
{opt b2title()}, {opt l1title()}, {opt l2title()}, {opt r1title()} and
{opt r2title()} ({cmd:t()}, {cmd:b()}, {cmd:l()} and {cmd:r()} for the
{cmd:1} titles) are drawn where {cmd:twoway} draws them, in both render
modes: the {cmd:t} titles above the plot region, the {cmd:b} titles
below it, the {cmd:l} titles to its left and the {cmd:r} titles to its
right, turned on their side.  The {cmd:1} title is nearest the plot and
the {cmd:2} title outside it, both outside every axis on that side and
inside the legend, the note, the caption, the subtitle and the title
({cmd:twoway}'s rings 1 and 2).  Each is the scheme's
{cmd:textboxstyle t1title} ... {cmd:r2title} box -- under {cmd:s2color}
{cmd:subheading} for the {cmd:1} titles and {cmd:body} for the {cmd:2}
titles, except {cmd:b2title()}, which {cmd:twoway} draws in
{cmd:b1title()}'s box, as {cmd:dash} does.  {cmd:size()}, {cmd:color()},
{cmd:prefix} and {cmd:suffix} are honoured as on {cmd:title()}.
{cmd:position()} moves an edge title to that clock, level, by the clock
rule of {help dash##textbox_options:Textbox options}
({cmd:l1title("E", position(12))} is above the plot), and {cmd:ring()}
orders it on its side ({cmd:ring(8)} is outside the title; {cmd:ring(0)}
stays nearest the plot, as in {cmd:twoway}); {cmd:span} and
{cmd:nospan} are refused, {cmd:option(s) t1title_span(yes) not allowed},
{cmd:r(198)}, as {cmd:twoway} refuses them; {cmd:orientation()} and the
other text-box sub-options are named in the note.  On a {cmd:by()} graph
each panel carries them, as {cmd:twoway} draws them.

{marker textbox_options}{...}
{pstd}
{ul:Textbox options.}  On {cmd:title()}, {cmd:subtitle()}, {cmd:note()}
and {cmd:caption()}, besides {cmd:size()}, {cmd:color()}, {cmd:prefix}
and {cmd:suffix}, these sub-options are drawn where {cmd:twoway} draws
them, in both render modes, and nothing is printed for them:
{cmd:position()}, {cmd:ring()}, {cmd:span}, {cmd:justification()},
{cmd:alignment()}, {cmd:margin()}, {cmd:linegap()}, {cmd:box},
{cmd:nobox}, {cmd:bcolor()}, {cmd:fcolor()}, {cmd:bfcolor()},
{cmd:lcolor()}, {cmd:lwidth()}, {cmd:lpattern()}, {cmd:bmargin()},
{cmd:bexpand}, {cmd:tstyle()} and {cmd:placement()}.
{cmd:position(}{it:#}{cmd:)} is the clock: 11, 12 and 1 above the plot
region, 5, 6 and 7 below it, at the left, centre or right.
{cmd:twoway} draws a box at 2, 3 or 4 o'clock to the right of the plot
and one at 8, 9 or 10 o'clock to its left; {cmd:dash} draws it on the
nearer horizontal side, at the right or left -- {cmd:title("T",}
{cmd:position(3))} is below the plot at the right -- because a title in
a side panel is turned on its side.  {cmd:ring()} orders the boxes on
one side, a larger ring further out: the title is ring 7, the subtitle
6, the caption 5, the note 4 (the scheme's {cmd:gridringstyle}
{it:box}{cmd:_ring}), the legend 3 and the edge titles 1 and 2.
{cmd:ring(0)} or {cmd:position(0)} draws the box inside the plot region
at the clock's compass point ({cmd:position(0)} its centre), and
{cmd:span} there prints {cmd:twoway}'s note "option span ignored for
position(0)".  {cmd:box} frames the text: {cmd:bcolor()} colours the
fill and the line, {cmd:fcolor()} and {cmd:bfcolor()} the fill,
{cmd:lcolor()}, {cmd:lwidth()} and {cmd:lpattern()} the line; as in
{cmd:twoway} they draw nothing without {cmd:box}, and {cmd:nobox}
removes a scheme's box.  {cmd:margin()} pads the text, {cmd:linegap()}
adds to the line step (the font size), {cmd:justification()} aligns the
text inside its box (the box stays at its clock, as in {cmd:twoway}),
{cmd:alignment()} sets its vertical place, {cmd:bmargin()} the gap to
the plot and {cmd:placement()} the anchor of a box inside the plot
region.  {cmd:tstyle()} is the base style -- {cmd:tstyle(heading)}
draws the heading's size and colour -- and {cmd:size()} and
{cmd:color()} still win; an unknown name draws the default with
{cmd:twoway}'s note "named style ... not found in class textboxstyle,
default attributes used".  A box is its text and its text box style's
margin, as {cmd:twoway} draws it ({cmd:vsmall}, 0.6 units, for the four
under {cmd:s2color}), unless {cmd:margin()} gives another.  {cmd:span}
places a box above or below the plot on the whole graph instead of the
plot region, as {cmd:twoway} draws it -- centred on the graph region's
width, or against its left or right edge by the gap the box keeps from
the plot region without {cmd:span} -- in the saved page and the served app and
after a resize; a box {cmd:twoway} draws beside the plot (2-4 or 8-10
o'clock, which {cmd:dash} draws above or below it) keeps its place.  On
a {cmd:by()} graph, {cmd:by()}'s own spanned {cmd:title()}, {cmd:note()}
and {cmd:caption()} are placed on the whole {cmd:by()} graph, and a
spanned {cmd:title()} or {cmd:note()} given outside {cmd:by()}, which is
drawn on every panel, on that panel (from just left of its y labels to
the scheme's {cmd:by()} panel margin past its plot region on the right), as
{cmd:twoway} draws them.  {cmd:bexpand} is taken.  {cmd:orientation()}, {cmd:width()},
{cmd:height()}, {cmd:angle()}, {cmd:lstyle()} and the {cmd:bl}...
sub-options are named in the note: a title box has no angle and no fixed
size.  On a {cmd:by()} graph a panel's label row takes {cmd:position()},
{cmd:ring()}, the box colours and {cmd:box}/{cmd:nobox}, as {cmd:twoway}
places and fills it (see Faceting with {cmd:by()}), and names the other
placement and box sub-options.


{marker colorvar}
{title:Mapping a Variable to Colour}

{pstd}
{cmd:colorvar(}{it:varname}{cmd:)} colours each observation of a layer by a
third variable instead of by the scheme's series colour.  {cmd:dash} draws
it on every plot type twoway colours -- markers, bars, spikes, drop lines,
range bars and caps, and the shafts and heads of the paired-coordinate
arrows, are coloured observation by observation, with one colour key a
layer; a line ({cmd:line}, {cmd:rline}'s bounds, {cmd:tsline},
{cmd:tsrline}, the connecting line of {cmd:connected} and
{cmd:rconnected}) is drawn as {cmd:twoway} draws it, one line a colour
level joining that level's observations in the line's order, the
observations missing the variable a line of their own in the
{cmd:colorformissing()} colour, before and after a filter move (a continuous
{cmd:colorvar()} takes {cmd:twoway}'s levels: its cuts are the key's labels,
a label below the variable's minimum dropped, and each level, up to and
including a cut, one colour of the key, on the line and on the markers of
{cmd:connected} and {cmd:rconnected}; under {cmd:zscale(log)} the levels are
the same and the key is drawn on a log scale in their colours, as
{cmd:twoway} draws it) (measured: on
{it:x} 1 to 6 with levels 1 1 2 2 1 3, one line through the 1st, 2nd and
5th points, one through the 3rd and 4th, and nothing for the 6th alone).
On {cmd:area}, {cmd:rarea}, the fits and
smooths, {cmd:kdensity}, {cmd:histogram}, {cmd:function}, {cmd:scatteri},
{cmd:pci} and {cmd:pcarrowi}, {cmd:twoway} drops {cmd:colorvar()} without a
word -- and without looking the variable up -- and so does {cmd:dash}.
With more than one y variable, {cmd:colorvar()} is refused on
{cmd:scatter}, {cmd:line}, {cmd:tsline}, {cmd:bar}, {cmd:connected},
{cmd:dot}, {cmd:dropline} and {cmd:spike}, as {cmd:twoway} refuses it.

{synoptset 38}{...}
{synopt:{cmdab:colorv:ar(}{it:varname}{cmd:)}}colour each observation by
    {it:varname}, a numeric variable, as in {cmd:twoway}{p_end}
{synopt:{cmdab:colordis:crete}}treat {it:varname} as categorical: one
    colour per value{p_end}
{synopt:{cmdab:colorcut:s(}{it:numlist}{cmd:)}}explicit break points for the
    colour bins{p_end}
{synopt:{cmdab:colorlev:els(}{it:#}{cmd:)}}# levels: # - 1 equally spaced cuts
    between the minimum and maximum; as in {cmd:twoway}, 0 and 1 draw as if it were absent, and a
    negative number or one over 100 draws 5 levels{p_end}
{synopt:{cmdab:colorvarminm:ax}}add the minimum and maximum of {it:varname} to
    the cuts, and to the colour bar's ticks{p_end}
{synopt:{cmdab:colorr:ule(}{it:rule} [{cmd:%}{it:#}] [{cmd:*}{it:#}]{cmd:)}}how
    the level colours are made: {cmd:hue} (equally spaced hues from
    {cmd:colorstart()} to {cmd:colorend()}), {cmd:chue} (the hues the other
    way round the wheel), {cmd:phue} (the scheme's p1, p2, ...),
    {cmd:intensity} (equally spaced intensities of {cmd:colorend()}),
    {cmd:linear} or {cmd:revlinear} (RGB from start to end, or end to
    start); {cmd:%}{it:#} an opacity and {cmd:*}{it:#} an intensity for
    every level{p_end}
{synopt:{cmdab:colorst:art(}{it:color}{cmd:)}}the rule's first colour{p_end}
{synopt:{cmdab:colore:nd(}{it:color}{cmd:)}}the rule's last colour{p_end}
{synopt:{cmdab:colorli:st(}{it:colors}{cmd:)}}one colour a level, in order;
    a list shorter than the levels repeats its last colour{p_end}
{synopt:{cmd:colorfillonly}}colour the fills only; outlines keep the series
    colour{p_end}
{synopt:{cmdab:colorformiss:ing(}{it:color}{cmd:)}}colour drawn for
    observations where {it:varname} is missing{p_end}
{synopt:{cmdab:colorkeysran:ge}}draw each key entry's swatch as a
    bar{p_end}
{synopt:{cmdab:colorkeysrev:erse}}reverse the order of the key's levels{p_end}
{synopt:{cmd:colorallowmultiple}}allow this {cmd:colorvar()} layer beside an
    earlier one; without it the second is refused, as {cmd:twoway} refuses
    it{p_end}
{synopt:{cmdab:colorotherlab:el(}{it:text}{cmd:)}}the text of the key's gray
    entry, the missing values and every value no level takes{p_end}
{synopt:{cmdab:colorusepleg:end}}the keys in the plot legend, placed by
    {cmd:plegend()}; it needs {cmd:colordiscrete}, as in {cmd:twoway}{p_end}
{synoptline}

{pstd}
The graph options {cmd:clegend()}, {cmd:plegend()} and {cmd:pcycle()} go
with it.  {cmd:clegend(}{it:suboptions}{cmd:)} places the colour key:
{cmd:off}, {cmd:position()} (the key stays upright, below the plot at 6
o'clock, as in {cmd:twoway}), {cmd:ring()} ({cmd:ring(0)} inside the
plot at the position, the scheme's 3 o'clock unless {cmd:position()} is
given; a ring inside the legend's 3 between the plot and the legend, as in
{cmd:twoway}; the scheme's {cmd:gridringstyle zyx2legend_ring} where
{cmd:ring()} is not given), {cmd:title()}, and on the colour bar {cmd:width()} and {cmd:height()}; its
other sub-options are named in the note.  {cmd:plegend()} does the same for
the keys {cmd:coloruseplegend} puts in the plot legend, where
{cmd:clegend()} has no key to place and is named.  {cmd:pcycle(}{it:#}{cmd:)}
is the number of plot styles before {cmd:p1} recurs:
{cmd:scatter mpg trunk turn weight, pcycle(2)} draws its third series in {cmd:p1}.  Series
{it:k} (a confidence-interval fit counting two) draws in
{cmd:p}{it:m}, {it:m} = mod({it:k}-1, {it:#})+1, as in {cmd:twoway}, so a
fraction is drawn while every {it:m} is whole -- {cmd:pcycle(1.5)} on one or
two series, {cmd:pcycle(0.5)} on any number, all in {cmd:p1} -- and
refused, as {cmd:twoway} refuses it ("option seriesid() not allowed"),
where one is not, or when {it:#} is 0 or less.
{marker pnum}{cmd:p1()} to {cmd:p20()} after the comma give their options to
the plot of that number, each y of a varlist counted and a
confidence-interval fit counted once, and {cmd:p}{it:#}{cmd:()} inside a
plot gives them to its {it:#}th y, as {cmd:twoway} draws them: the plot's
own options win over them, a later one wins over an earlier one, a number
with no such plot or y changes nothing, and {cmd:p21()} and above are
refused as {cmd:twoway} refuses them
({cmd:p21(mcolor(red)):  too many arguments}, r(103)); for one y of
several only the style options are drawn, and any other, or a
{cmd:p}{it:#}{cmd:()} that names a confidence-interval fit's own band or
line, is named in the note.
{cmd:colorvar(i.}{it:varname}{cmd:)} is
{cmd:colorvar(}{it:varname}{cmd:) colordiscrete coloruseplegend}, as in {cmd:twoway}.

{pstd}
{cmd:colorvar()}, {cmd:colordiscrete}, {cmd:colorcuts()},
{cmd:colorlevels()} and {cmd:colorvarminmax} are Stata 18's own and drawn as
Stata draws them: under {cmd:colordiscrete} the cuts are the levels and every
other value is drawn in {cmd:colorformissing()}'s colour with the missing
values; a cut below the minimum is ignored, and the minimum is used if all
are; {cmd:colorcuts()} and {cmd:colorlevels()} may not be combined.
Every other
{cmd:colorvar} option {cmd:twoway} takes is drawn, in {cmd:twoway}'s
colours (measured to 1/255 a channel): with no {cmd:colorrule()},
{cmd:colorstart()} or {cmd:colorend()}, the scheme's rule -- hue from blue
to red under {cmd:s2color} and {cmd:stcolor}, intensity of black under the
mono schemes; under a scheme of your own, the rule of the shipped scheme it
includes, with its own {cmd:zyx2rule contour}, {cmd:color contour_begin},
{cmd:color contour_end} and {cmd:shadestyle contour_begin} or
{cmd:contour_end} lines read as Stata reads them (a hue keeps the begin
colour's saturation and value, so green to orange is drawn at green's
darkness); {it:k} levels of {cmd:colordiscrete} take the first {it:k}
of {it:k}+1 steps, {it:k} bins {it:k} steps.  {cmd:colorlist()} wins, then
the rule.  A rule's name abbreviates as
{cmd:twoway}'s does: {cmd:colorrule(lin)} is {cmd:colorrule(linear)},
{cmd:colorrule(int)} {cmd:colorrule(intensity)} and {cmd:colorrule(revlin)}
{cmd:colorrule(revlinear)}, in {cmd:crule()} too; a name {cmd:twoway} has
no rule for, such as {cmd:colorrule(hsv)}, is refused as {cmd:twoway}
refuses it when it draws, after its two notes, {cmd:r(198)}.
{cmd:colorkeysreverse} reverses a
{cmd:colordiscrete} key; on any other key -- a colour bar, binned by
{cmd:colorlevels()} or with {cmd:colorkeysrange} -- {cmd:twoway} draws the
same key with it as without it, and so does {cmd:dash}, in silence; under
{cmd:coloruseplegend} it is taken in silence too, as {cmd:twoway}'s plot
legend keeps its order.  How the colours are drawn
is {cmd:dash}'s: an unbinned numeric {it:varname} is mapped continuously
through the rule's colours in 256 steps and a colour bar is drawn beside
the figure, where
{cmd:twoway} bins it at its z axis's ticks.  The colour bar sits on the
graph region with no box of its own: its tick labels take the scheme's
{cmd:tick_label} size and colour, its title the {cmd:axis_title} size and
colour, upright, and its ticks the scheme's tick colour, width and length,
as in {cmd:twoway}'s colour key.  {cmd:twoway} turns the title to run up
the key's right-hand side and draws an axis line on the side of its
labels; {cmd:dash} draws the title above the bar and no axis line.
{cmd:colordiscrete},
{cmd:colorcuts()} and {cmd:colorlevels()} bin it, and a discrete key
entry is drawn per bin, in the rule's colours unless
{cmd:colorlist()} names others.  A string {it:varname} is refused as
{cmd:twoway} refuses it ({cmd:'make' found where numeric variable expected},
r(7)).

{pstd}
{ul:Which observations set the colours.}  The colours, the colour bar's
range, the cuts of {cmd:colorcuts()} and {cmd:colorlevels()}, the levels of
{cmd:colordiscrete} and a string variable's categories ({cmd:dash}'s own;
{cmd:twoway} stops with r(7)) come from the observations the plot draws, as
{cmd:twoway} takes them: those its own {cmd:if} and {cmd:in}, the graph's
{cmd:if} and {cmd:in} and, under {cmd:by()}, its panel select.  An
observation whose y or x is missing counts too.  So in {cmd:sysuse auto}, a
scatter of {cmd:mpg} on {cmd:weight} with its own {cmd:if foreign==1} and
{cmd:colorvar(price)}, drawn beside a scatter of the domestic cars, spans
3,748 to 12,990, the prices of the foreign cars.  Under {cmd:by()}
each panel colours its own observations, as {cmd:twoway} does, and, as in
{cmd:twoway}, no panel draws a key: {cmd:by(, clegend(on))} draws one,
the first panel's.  After a filter move a key of the variable's own levels
({cmd:colordiscrete}, a string variable) is levelled again over the
observations kept, as {cmd:twoway} levels the observations it draws: the
levels left take the first colours, each panel its own and
{cmd:by()}'s key the first panel's, in both the saved page and the served
app; a continuous key's colours span the observations kept and its labels
are ticked over them -- by {cmd:zlabel(#}{it:N}{cmd:)} or
{cmd:zlabel(minmax)} when given, and over a date's values in its Stata
units -- and a line's colour levels are cut at those labels, under
{cmd:zscale(log)} too, and {cmd:colorlevels()} cuts the observations
kept again and {cmd:colorcuts()} keeps its cuts at or above their
minimum, each {cmd:by()} panel over its own and a line's levels with
them, as in {cmd:twoway}; labels {cmd:zlabel()} lists or steps keep
their values.  The observations kept are those the plot colours, an
observation whose y or x is missing included, a plot with its own
{cmd:if} or {cmd:in} too, and under {cmd:colorvarminmax} a
{cmd:colorcuts()} key can gain the bin a move leaves, as {cmd:twoway}'s
does.
{cmd:rconnected} draws one key for both ends.  A plot whose {cmd:if}
selects no observation draws no key ({cmd:twoway} stops with r(3001)), and
one whose observations are all missing on the variable draws a
"(missing)" entry where {cmd:twoway} draws the key's title alone.

{pstd}
The colour key's own axis options, {cmd:ztitle()}, {cmd:zlabel()} and
{cmd:zscale()}, are taken as graph options and drawn on the key: the title on
either key; ticks, {cmd:#}{it:N}, {cmd:none} and {cmd:minmax}, and
{cmd:range()} (widening only), {cmd:log} and {cmd:reverse}, on the colour bar.
{cmd:zlabel(, labsize())} is drawn on the colour bar's labels.
The key's numbers are {it:varname}'s values in its own units, written as
{cmd:twoway} writes its colour key: in {cmd:%8.0gc} whatever {it:varname}'s
display format ({cmd:5,000} for a {cmd:%9.0g} {cmd:price}), or in
{cmd:zlabel(, format())}'s format -- on the colour bar, in a binned key's
bounds and in a discrete key's levels.  The colour bar is ticked where
{cmd:twoway} ticks its key, by the rule of {cmd:#5} over the plotted values,
and {cmd:#}{it:N}, {cmd:minmax}, a list of values, {cmd:colorcuts()},
{cmd:colorlevels()} and {cmd:range()} are read in the same units.  So a date
variable keys {cmd:15,000} ... {cmd:15,400} and {cmd:colorcuts(15100 15200)}
cuts at those days, as in {cmd:twoway}; {cmd:zlabel(, format(%td))} writes
the dates.  A format {cmd:twoway} accepts that {cmd:dash} cannot write
({cmd:%12s}, {cmd:%21x}) is drawn as {cmd:%9.0g} and named in the note.
On a discrete key {cmd:zlabel()}'s ticks and {cmd:zscale()} are named in the
note.
{cmd:ztitle()} given only sub-options styles the key's default title, the
colour variable's label; {cmd:suffix} and {cmd:prefix} add lines to it.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, colorvar(price) colorlevels(8)}{p_end}

{pstd}
{ul:When a legend appears.}  As in {helpb twoway}, a legend is drawn only
when the graph has two or more keys: a lone {cmd:scatter} gets none, a
{cmd:scatter} with an {cmd:lfit} over it gets one.  {cmd:legend(on)} forces
one onto a single-key graph and {cmd:legend(off)} removes it from any graph;
in one {cmd:legend()}, {cmd:on} wins over {cmd:off}.
Plots that look the same, none given a style option of its own, share one
key, the first plot's, its text their texts joined by "/", as
{cmd:twoway} draws them: two histograms, of {cmd:mpg} and of {cmd:price},
are one key, "Density", in the one histogram colour, so they draw no
legend; scatters of {cmd:mpg} and {cmd:price} with {cmd:pstyle(p1)} are one
key, "Mileage (mpg)/Price"; {cmd:color(red)} on one histogram, or
{cmd:mcolor()} or {cmd:msize()} on a scatter -- even the size it would
have drawn -- keeps its key apart, while {cmd:mlabel()} does not.  The
merged key answers to the first plot's number: {cmd:label(1 "A")} renames
it, and {cmd:label(2 "B")} and {cmd:order(2)} find no key, as in
{cmd:twoway}.
A {cmd:colorvar()} key is not the legend: it stays.
{cmd:legend()}'s sub-options are read under {cmd:twoway}'s spellings in
lower case: {cmd:legend(c(2) r(1) lab(1 "A") posi(6) s(small) lastlab(2 "Z"))}
draws as its full names, and in {cmd:legend(cols(1) c(red))} the second
spelling is {cmd:color(red)}.  What {cmd:twoway}
refuses is refused with its return code and words -- {cmd:legend(OFF)},
{cmd:legend(po(9))}, {cmd:legend(c(2) cols(1))}, {cmd:legend(c(red))}
(r(121)), {cmd:legend(label(0 "A"))} -- and where {cmd:twoway} draws the
default with a note, so does {cmd:dash}, once: a {cmd:position()} outside
0-12, a non-numeric {cmd:ring()}, an {cmd:order()} holding a word that is
no integer (the whole {cmd:order()} is ignored).  {cmd:rows()} wins over
{cmd:cols()}.


{marker geometry}
{title:Figure proportions}

{pstd}
A {cmd:dash} dashboard is responsive: figures stretch to the width they are
given rather than being drawn at a fixed pixel size.  {cmd:xsize()},
{cmd:ysize()} and {cmd:aspectratio()} therefore set a figure's PROPORTIONS,
and the figure fills the width available at that shape.  At phone width a
grid too narrow for its columns stacks them, so each figure takes the whole
width (see {help dash##layout:Layout}).

{pstd}
The precedence, highest first:

{phang2}1. {cmd:xsize()} and {cmd:ysize()}, in inches, as in Stata.  Either
    alone keeps the other from the scheme: under {cmd:stcolor},
    {cmd:xsize(9)} gives a graph 9 inches wide and 4.5 tall, exactly as
    {helpb twoway} does.{p_end}
{phang2}2. {cmd:aspectratio(}{it:#}{cmd:)}, which in Stata is
    {bf:height divided by width} -- {cmd:aspectratio(0.5)} is half as tall as
    it is wide.{p_end}
{phang2}3. The active scheme's {cmd:graphsize x} and {cmd:graphsize y}, so a
    {cmd:dash} dashboard has the proportions of your other graphs without
    your asking.{p_end}

{pstd}
Under {cmd:by()}, as in {helpb twoway}, {cmd:xsize()} and {cmd:ysize()}
size the whole graph, not each panel: the axis titles, a legend or colour
key at 6 or 12 o'clock and {cmd:by()}'s title, note and caption take their
rows from the panels, which grow shorter, so the graph keeps its ratio;
{cmd:layout(bs)} places a faceted graph by that ratio.

{phang2}{opt aspectratio(#)} shapes the {bf:plot region}, as in
{helpb twoway}, and takes {helpb twoway}'s sub-option {it:placement}
({it:compassdir}) after a comma.  With {cmd:xsize()} or
{cmd:ysize()} the figure is drawn at that size (96 pixels an inch, held to
the page's height bound) and its plot region is the largest of ratio
{it:#} that fits, placed where {it:placement} says -- {cmd:e} against
the right edge, {cmd:w} the left, {cmd:n} the top, {cmd:s} the bottom,
{cmd:c} (the default) centred; a name {cmd:twoway} does not know is noted
and centred, as {cmd:twoway} draws it.  The figure is drawn at that size;
the room the axes and titles take is estimated, up to 4 pixels high for
each line of a title, so the plot region, always of ratio {it:#}, can be
that much smaller than the largest that fits.  Such a figure keeps its size
in a cell narrower than it, which then scrolls sideways.  Without {cmd:xsize()} or {cmd:ysize()} the figure stretches to
its cell, so {it:#} shapes the whole figure instead (the plot region's
own ratio then differs from {it:#} by the room the axes take), and
{it:placement} has no slack to use.  Under {cmd:by()} {it:#} shapes
each panel as a figure.{p_end}

{phang2}{opt scale(#)} multiplies every text size, marker size and line
width of the graph -- titles, axis titles, tick labels and tick lengths,
legend keys and labels, added text, reference lines -- by {it:#}, as in
{helpb twoway}, and with them the gaps around titles, labels, keys and
added text; only the graph region's margins stay as they are.  dash's
differences are listed under
{help dash##differences:Differences from twoway}.  {cmd:scale(0)} draws
every size at 0 and a negative {it:#} is refused, r(198), in
{cmd:twoway}'s words; a word is noted and drawn at 1.{p_end}

{phang2}{opt fysize(#)} draws the figure {it:#} percent as tall, and
{opt fxsize(#)} holds it to {it:#} percent of the width its cell
gives it.  {helpb twoway} keeps a graph drawn alone at its size and draws
the plot in {it:#} percent of four inches, centred; on a dashboard the cell
is what shrinks.  A value of 0 or less, or of 100 and more, changes
nothing; a word is refused, r(198), as {cmd:twoway} refuses it.  Both
may be shortened to five letters, as in {cmd:twoway}.{p_end}

{phang2}{opt xoverhangs} and {opt yoverhangs} keep the first and last tick labels
inside the figure, as {helpb twoway} narrows the plot region for them: the
figure's border on each side is raised to half the widest end label, never
lowered.  {cmd:aspectratio()} with {cmd:xoverhangs} or {cmd:yoverhangs} is
refused, as {cmd:twoway} refuses it.{p_end}

{pstd}
{it:The size reference.}  As in {helpb twoway}, a relative size -- a number,
or a name such as {cmd:medium} -- is a share of the smaller side of the
graph: one unit is 2.88 points at four inches, and {cmd:dash}, whose
figures the browser sizes, draws it at 2.88 points whatever the graph's
size.  An absolute size -- {it:#}{cmd:pt}, {it:#}{cmd:in}, {it:#}{cmd:cm},
and a scheme's own point sizes -- keeps its length on a graph of any size,
so it is converted at the figure's reference: the smaller of
{cmd:xsize()} and {cmd:ysize()}, the scheme's {cmd:graphsize} standing in
for one not given, and the smaller scheme side with neither.  So
{cmd:title("T", size(14pt)) xsize(8) ysize(8)} draws the title at half the
share of the figure it takes at four inches, as {helpb twoway} does, and
{cmd:size(5)} the same share of both.  {cmd:scale()} multiplies afterwards
and never moves the reference.

{pstd}
The ratio is honoured within a height band.  Outside it the ratio yields, so
that a single square panel cannot fill an entire screen and a very wide panel
does not collapse to an unreadable sliver on a phone.

{pstd}
{it:Examples:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xsize(10) ysize(2)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, aspectratio(1)}{p_end}

{pstd}
{it:Examples:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xtitle(Weight (lbs)) ytitle(Mileage)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xscale(log) yscale(log)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xline(3000) yline(20 30)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, xlabel(1000 2000 3000 4000) ylabel(10 20 30 40)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, note(Source: 1978 Automobile Data)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, aspectratio(0.75)}{p_end}


{marker markers}
{title:Marker and Transparency Options}

{pstd}
{marker colours}{ul:Colours.}  Every colour option reads Stata's colour
grammar, in the saved dashboard and the served app alike: a colour name,
case-sensitive ({cmd:navy}; {cmd:Navy} is not a name, nor are {cmd:grey}
and the other British spellings); an RGB triplet {cmd:"R G B"}; CMYK
{cmd:"C M Y K"} (proportions from 0 to 1, or whole numbers from 0 to 255);
HSV {cmd:"hsv H S V"}; a hex code {cmd:#rrggbb}; and {cmd:bg}, {cmd:fg},
{cmd:background} and {cmd:foreground}, the scheme's background and
foreground colours, when the scheme names them.  {it:colour}{cmd:*}{it:#}
sets the intensity, lighter below 1 and darker above it (multiplied under
a scheme's {cmd:system naturally_white 0}), and {it:colour}{cmd:%}{it:#}
the opacity, from 0 to 100; the two may be given in either order.  An
unknown colour, or a number out of range, is drawn black (a bar or an
area at its intensity), as {cmd:twoway} draws it, with {cmd:twoway}'s note,
{cmd:(note:  dash: named style }{it:name}{cmd: not found in class color, default attributes used)},
{it:name} the colour as written, its {cmd:*}{it:#} and {cmd:%}{it:#} left
off; a malformed hex code, multiplier or opacity keeps the default in
silence; a colour written with commas is read as {cmd:twoway} reads it
(see {help dash##validation:Option values}).  A bare
{cmd:*}{it:#}, {cmd:%}{it:#} or both, with no colour of its own, adjusts
the colour the element would draw without the option, as {cmd:twoway}
does, at every colour option: {cmd:mcolor(*.5)} lightens the marker's
own colour (a named style's included), {cmd:fcolor(*.7)} on a bar
lightens the bar's colour before the bar's intensity is applied, and
{cmd:title("T", color(*.5))} lightens the scheme's title colour.  A
{cmd:%}{it:#} sets that element's opacity wherever it is written; without
one, the scheme's own opacity is kept.

{pstd}
These plot-level options are honoured on the plot types named, in the
saved dashboard and the served app alike, and {cmd:dash}'s note does not
name them there.

{synoptset 28}{...}
{synopt:{opt jitter(#)}}move each marker by uniform noise
    spanning {it:#}% of the data's range on each axis; {it:#} must be a
    number from 0 to 100, or a list of them, one per y (see
    {help dash##stylelists:Style lists}).  Drawn on the markers of {cmd:scatter},
    {cmd:connected}, {cmd:rconnected}, {cmd:dot}, {cmd:dropline},
    {cmd:scatteri}, {cmd:rscatter}, {cmd:rcapsym}, {cmd:rpcap}, {cmd:rpspike},
    {cmd:pcscatter} and
    {cmd:pccapsym} (both ends), never on a connecting line or a spine, as
    in {cmd:twoway}.  As in {cmd:twoway}, the name is not abbreviated:
    {cmd:jit()} is refused{p_end}
{synopt:{opt jitterseed(#)}}random-number seed for {cmd:jitter()}, spelled as
    in Stata; {it:#} must be a non-negative integer.  With no seed the noise
    differs on every render{p_end}
{synopt:{cmdab:msa:ngle(}{it:#}{cmd:)}}rotate every marker in the layer
    {it:#} degrees counter-clockwise, as {cmd:twoway} does; {it:#} must lie
    between -360 and 360, as in {cmd:twoway}, or be one of Stata's
    anglestyles ({cmd:horizontal}, {cmd:vertical}, {cmd:rvertical},
    {cmd:rhorizontal}, {cmd:forty_five}, ...).  Drawn on every plot type
    that draws markers: {cmd:scatter}, {cmd:connected}, {cmd:rconnected},
    {cmd:dot}, {cmd:dropline}, {cmd:scatteri}, {cmd:rscatter},
    {cmd:rcapsym}, {cmd:rpcap}, {cmd:rpspike}, {cmd:pcscatter} and
    {cmd:pccapsym}{p_end}
{synopt:{cmdab:col:or(}{it:color}{cmd:)}}the layer's colour -- its markers,
    lines and fills alike, as in {cmd:twoway}; {cmd:mcolor()},
    {cmd:lcolor()} and {cmd:fcolor()} win where given{p_end}
{synoptline}

{pstd}
Opacity is Stata's {cmd:color%alpha} notation: {cmd:mcolor(red%50)},
{cmd:lcolor(%40)} and {cmd:fcolor(ltblue%40)}.

{pstd}
Markers are drawn opaque, as {cmd:twoway} draws them, unless a colour's
{cmd:%}{it:NN} or a scheme's declared opacity ({cmd:sttrans}'s {cmd:%20})
asks for one.  A {cmd:bar}, {cmd:rbar}, {cmd:area} or
{cmd:rarea} fill is its colour at the layer's intensity (the scheme's
{cmd:intensity p}{it:#}{cmd:bar} or {cmd:intensity p}{it:#}{cmd:area},
{cmd:inten80} in the shipped schemes), opaque, so {cmd:s2color}'s bar is
#486C8C and {cmd:fcolor(yellow)} fills #FFFF33.  {cmd:fintensity()}
replaces that intensity and is drawn as {cmd:twoway} draws it: blended
towards white below 100 and darker above it ({cmd:fintensity(150)} divides
each channel by 1.5); towards black under {cmd:s1rcolor}, whose scheme is
not naturally white; 0 and negative values draw white (almost black under
{cmd:s1rcolor}); {cmd:fintensity(.)} draws the layer's own intensity.
{cmd:inten0} to {cmd:inten100}, {cmd:inten200}, {cmd:full} and {cmd:max}
are the names; any other name draws full intensity with a note, and no
value is refused.  A histogram is filled at full intensity.  A brushed-away
fill is dimmed in its own colour.

{pstd}
The line options {cmd:lcolor()} and {cmd:lwidth()} style a
layer's lines -- a connecting line, a drop, a spike -- and never its
markers, as in {cmd:twoway}: a marker's outline is {cmd:mlcolor()} and
{cmd:mlwidth()}, and {cmd:color()} colours markers, lines and fills
alike.  An unknown {cmd:lcolor()} or {cmd:lwidth()} name is still reported
on a plot with no line, as {cmd:twoway} notes it there.

{pstd}
{ul:Line widths.}  A line width is drawn in Stata's units, on Stata's own
ladder: {cmd:none}, {cmd:vvvthin}, {cmd:vvthin}, {cmd:vthin}, {cmd:thin},
{cmd:medthin}, {cmd:medium}, {cmd:medthick}, {cmd:thick}, {cmd:vthick},
{cmd:vvthick} and {cmd:vvvthick}, from 0 to 4.2 units, {cmd:medium} being
0.30.  One unit is 2.88 points at the four-inch reference, as for every
other size, so {cmd:lwidth(thick)} draws 8/3 as wide as {cmd:medium}.  A
number and {it:#}{cmd:rs} are Stata units; {it:#}{cmd:pt}, {it:#}{cmd:in}
and {it:#}{cmd:cm} are absolute, at the graph's reference length;
{cmd:*}{it:#} multiplies the width the site would draw otherwise, before
the floor: {cmd:xline(3000, lwidth(*2))} under a scheme whose {cmd:xyline}
is {cmd:vvthin} draws the floor, as {cmd:twoway} does, not twice it; the
same holds for {cmd:tlwidth()}, {cmd:glwidth()} and the axis line's
{cmd:lwidth()}, which multiply the scheme's tick, grid and axis widths.  A
width under 0.3 point is drawn at 0.3 point, as {cmd:twoway} draws it,
and {cmd:none}, {cmd:0} and {cmd:*0} draw nothing.  A name is matched in
its case, so {cmd:lwidth(THICK)} is noted and drawn at the scheme's width,
as in {cmd:twoway}.  This holds for {cmd:lwidth()}, {cmd:mlwidth()},
{cmd:clwidth()}, {cmd:alwidth()}, {cmd:plotregion(lwidth())} and the
{cmd:lwidth()} of {cmd:xline()} and {cmd:yline()}, and for a scheme's
{cmd:linewidth} keys.  A {cmd:*}{it:#} or an absolute width whose value
passes 10000 units only once drawn, such as {cmd:lwidth(*40000)}, is
noted and drawn at the default, where {cmd:twoway} refuses it.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, jitter(5) jitterseed(12345) mcolor(%60)}{p_end}

{marker namedstyles}{...}
{pstd}
{bf:Named styles.}  These options draw the plot styles {cmd:p1} to
{cmd:p15} of the scheme as {cmd:twoway} draws them:{p_end}

{synoptset 24}{...}
{synopt:{cmdab:psty:le(}{it:p#}{cmd:)}}the whole plot{p_end}
{synopt:{cmd:p(}{it:p#}{cmd:)}}the whole plot, applied last (see below){p_end}
{synopt:{cmdab:mst:yle(}{it:p#}{cmd:)}}the markers{p_end}
{synopt:{cmdab:mls:tyle(}{it:p#}{cmd:)}}the markers' outlines{p_end}
{synopt:{cmdab:ls:tyle(}{it:p#}{cmd:)}}the lines{p_end}
{synopt:{cmdab:cls:tyle(}{it:p#}{cmd:)}}the connecting line of {cmd:line},
    {cmd:connected}, {cmd:tsline}, the fits and the smoothers{p_end}
{synopt:{cmdab:ast:yle(}{it:p#}{cmd:)}}a fill and its outline{p_end}
{synopt:{cmdab:al:style(}{it:p#}{cmd:)}}an outline{p_end}
{synopt:{cmdab:bst:yle(}{it:p#}{cmd:)}}a bar's fill and outline{p_end}
{synopt:{cmdab:bl:style(}{it:p#}{cmd:)}}a bar's outline{p_end}

{pstd}
The connecting line of the line types takes {cmd:pstyle()},
{cmd:lstyle()} and {cmd:clstyle()}; the lines of {cmd:spike}, the range
types, the paired-coordinate types and the outlines of {cmd:bar},
{cmd:rbar} and {cmd:histogram} take {cmd:pstyle()}, {cmd:lstyle()},
{cmd:astyle()}, {cmd:alstyle()}, {cmd:bstyle()} and {cmd:blstyle()}.  A
style option that a plot type does not draw is silent, as in
{cmd:twoway}.

{pstd}
A named style and your own options combine in {cmd:twoway}'s order: an
option wins over a style that comes before it in that order and loses to
one that comes after it, whatever order you type them in.  So
{cmd:mcolor(red) pstyle(p3)} draws red markers, {cmd:color(red) mstyle(p4)}
draws {cmd:p4}'s markers, and {cmd:lwidth(thick) lstyle(p3)} draws
{cmd:p3}'s line at {cmd:thick}.  {cmd:p()} is applied last: it restyles
the whole plot, the marker labels included, and discards every other
style option; the label text, {cmd:connect()} and {cmd:cmissing()} are
kept.  Its value is one name, and given twice the first copy wins.

{pstd}
Across a varlist of several y, {cmd:scatter y1 y2 x, pstyle(p3 p4)}
styles each y with its own element, as other style lists do;
{cmd:p()} is not split.  {cmd:pstyle(p}{it:#}{cmd:)} and
{cmd:p(p}{it:#}{cmd:)} also draw the layer as plot {it:#} for everything
the plot number colours (its marker labels and the immediate types
included); the layers after it keep their numbers.

{pstd}
Stata's other style names are drawn too, as {cmd:twoway} draws them under
the scheme: every line style ({cmd:lstyle(refline)}, {cmd:lstyle(grid)},
{cmd:lstyle(xyline)}, {cmd:lstyle(none)} ...), and {cmd:ci}, {cmd:ci2},
{cmd:histogram}, {cmd:none} and the {cmd:p}{it:#}{cmd:line},
{cmd:p}{it:#}{cmd:bar}, {cmd:p}{it:#}{cmd:area}, {cmd:p}{it:#}{cmd:box},
{cmd:p}{it:#}{cmd:dot} and {cmd:p}{it:#}{cmd:arrow} forms (see
{help dash##scheme:Stata scheme support}).  A name {cmd:twoway} does not
know draws its default attributes, with its note.

{pstd}
The outline of {cmd:area} and {cmd:rarea} takes {cmd:lstyle()},
{cmd:alstyle()} and {cmd:blstyle()}'s line style, and the arrowheads of
{cmd:pcarrow}, {cmd:pcbarrow} and {cmd:pcarrowi} take {cmd:mstyle()}
and {cmd:mlstyle()}'s, as {cmd:twoway} draws them; an explicit
{cmd:lcolor()}, {cmd:mcolor()} or {cmd:mlcolor()} is drawn over the
style, in either order.


{marker scheme}
{title:Stata scheme support}

{pstd}
{cmd:scheme()} applies a named Stata graph scheme to the whole dashboard.
A {cmd:scheme()} written on one graph draws that graph in it, in the
saved page and the served app alike; the page and the KPI cards take the
dashboard's scheme ({cmd:dash build}'s {cmd:scheme()}, then
{cmd:theme()}, then the first graph's, then {cmd:c(scheme)}).
With no {cmd:scheme()} and no {cmd:theme()}, {cmd:dash} follows the session's
own {cmd:c(scheme)}, so a dashboard has the look of every other graph you
draw without your asking.

{pstd}
A scheme whose {cmd:shadestyle plotregion} is {cmd:none} (s1color,
s1mono, s1rcolor, s1manual, stmono1) draws an unfilled plot region, as
{cmd:twoway} does; {cmd:plotregion(fcolor())} fills it.

{pstd}
{cmd:dash} ships faithful translations of twenty-six StataCorp schemes:

{synoptset 16}{...}
{synopt:{cmd:stcolor}}Stata's default as of Stata 18{p_end}
{synopt:{cmd:stcolor_alt}}{p_end}
{synopt:{cmd:stgcolor}}{p_end}
{synopt:{cmd:stgcolor_alt}}{cmd:stcolor_alt} at the manuals' page size{p_end}
{synopt:{cmd:stmono1}}{p_end}
{synopt:{cmd:stmono2}}{p_end}
{synopt:{cmd:stsj}}{p_end}
{synopt:{cmd:sttrans}}{cmd:s2color} restyled to {cmd:stcolor}'s look
    (white background, legend at the right) with a colourblind-friendly
    palette based on Paul Tol's muted colours, declared at twenty percent
    opacity ({cmd:%20}), which {cmd:dash} carries into the glyphs listed
    under {ul:Series} below, in both modes, as Stata draws it{p_end}
{synopt:{cmd:s2color}}Stata's default before Stata 18{p_end}
{synopt:{cmd:s2color8}}{cmd:s2color} with Stata's {cmd:8} colour variants
    ({cmd:navy8}, {cmd:ltbluishgray8}, {cmd:bluishgray8}) for the
    background, grid, boxes and the first and last series{p_end}
{synopt:{cmd:s2mono}}{p_end}
{synopt:{cmd:s2manual}}{cmd:s2mono} at the manuals' page size, used in
    Stata's manuals before Stata 13{p_end}
{synopt:{cmd:s2gmanual}}{cmd:s2mono} at the manuals' page size with each
    line plot in its own solid grey, used in [G] before Stata 13{p_end}
{synopt:{cmd:s2gcolor}}{p_end}
{synopt:{cmd:s1color}}{p_end}
{synopt:{cmd:s1mono}}{p_end}
{synopt:{cmd:s1manual}}{cmd:s1mono} at the manuals' page size, with larger
    markers{p_end}
{synopt:{cmd:s1rcolor}}light on a dark background{p_end}
{synopt:{cmd:economist}}{p_end}
{synopt:{cmd:sj}}{p_end}
{synopt:{cmd:meta}}{cmd:s2color} with smaller text (8-point tick labels
    where {cmd:s2color} has 10), thinner plot lines, a one-column legend at
    4 o'clock, and grids on both axes{p_end}
{synopt:{cmd:stcolor_meta}}{cmd:stcolor} with a solid cranberry
    {cmd:xline()}/{cmd:yline()}{p_end}
{synopt:{cmd:stcolor_mv}}{cmd:stcolor_alt} with solid reference lines{p_end}
{synopt:{cmd:stcoloralias}}{cmd:stcolor} with
    {cmd:zyx2rule colorvar hue}, a directive {cmd:dash} does not read: it
    is drawn as {cmd:stcolor}, which is also what {cmd:twoway} draws for a
    {cmd:colorvar()} scatter under it{p_end}
{synopt:{cmd:stgcolor_meta}}{cmd:stcolor_meta} at 3.987 by 2.392
    inches{p_end}
{synopt:{cmd:stgcolor_mv}}{cmd:stgcolor_alt} with solid reference
    lines{p_end}
{synoptline}

{pstd}
Each directive {cmd:dash} carries is consumed in the place Stata's
{cmd:graph} consumes it, and where it tells Stata to draw nothing -- a grid
the scheme turns off, say -- {cmd:dash} draws nothing.  The scheme sets:

{phang2}{ul:Regions.}  The background and plot-region colours
    ({cmd:color background}, {cmd:color plotregion}), the plot region's
    border ({cmd:color plotregion_line}, {cmd:linewidth plotregion}: the
    line Stata draws through {cmd:areastyle twoway_plotregion} -- white on
    white under {cmd:s2color} and {cmd:stcolor}, black under
    {cmd:s1color} and {cmd:s1mono}, none under {cmd:economist};
    {cmd:plotregion(lcolor())} still wins) and the figure
    proportions ({cmd:graphsize x}, {cmd:graphsize y}; see
    {help dash##geometry:Figure proportions}).{p_end}

{phang2}{ul:Reference lines.}  {cmd:xline()} and {cmd:yline()} are drawn
    in the scheme's {cmd:color xyline}, {cmd:linepattern xyline} and
    {cmd:linewidth xyline}, as {cmd:twoway} draws them: cranberry and solid
    under {cmd:s2color}, black and dashed under {cmd:stcolor}.  Their
    {cmd:lcolor()}, {cmd:lpattern()} and {cmd:lwidth()} still win, under
    {cmd:twoway}'s spellings too: {cmd:xline(5, lc(red) lp(dash) lw(thick))}.
    A line given the sub-option axis(2) is drawn at that value of the
    second axis; no line widens an axis.{p_end}

{phang2}{ul:Series.}  The colour, symbol and line-pattern cycles
    ({cmd:p1} to {cmd:p15}), the line width ({cmd:linewidth p}, and
    {cmd:linewidth p}{it:#} per plot), a marker's outline width (the
    same, or {cmd:linewidth p}{it:#}{cmd:mark} and {cmd:linewidth pmark}
    where a scheme declares them; {cmd:mlwidth()} still wins), a bar's
    and an area's outline width ({cmd:linewidth pbar} and
    {cmd:linewidth parea}; an area is outlined by default, as
    {cmd:twoway} outlines it), the
    marker fill and outline colours ({cmd:color p}{it:#}{cmd:markfill}
    and {cmd:color p}{it:#}{cmd:markline}, each falling back to
    {cmd:p}{it:#} as Stata's chain does; {cmd:color p}{it:#}{cmd:mark} is
    not read, as {cmd:twoway} does not read it), the
    marker size ({cmd:symbolsize p}, and {cmd:symbolsize p}{it:#} per
    plot), the fill intensities, and a colour
    opacity the scheme declares ({cmd:sttrans}'s {cmd:%20}), which is
    carried into every layer's lines, markers and fills in both modes, as
    Stata draws it, except the confidence band, which {cmd:twoway} draws
    in {cmd:color ci_area} with no opacity; a colour you give without its
    own {cmd:%}{it:NN} keeps the scheme's opacity, and
    {cmd:mcolor(}{it:x}{cmd:%}{it:NN}{cmd:)} still wins.
    A symbol in the cycle, or one you give with {cmd:msymbol()}, is drawn
    with its own traits: a hollow symbol ({cmd:circle_hollow} and the
    rest) as an outline, whatever a fill colour or its opacity say,
    and a small one ({cmd:smcircle}, {cmd:smdiamond}, {cmd:smsquare},
    {cmd:smplus}, {cmd:smx} and their hollow forms, and the shorthands
    {cmd:o}, {cmd:d}, {cmd:s}, {cmd:x} and {cmd:oh}, {cmd:dh}, {cmd:sh})
    at 0.71 of the full symbol's size, {cmd:smtriangle}, {cmd:t},
    {cmd:th}, {cmd:smv} and {cmd:v} at 0.75, and {cmd:lgx} at 1.41,
    after {cmd:msize()}, as Stata 19.5 draws them; every symbol is as
    tall against the circle as {cmd:twoway} draws it (a diamond 1.41 of
    the circle, a triangle, {cmd:V} and an arrow as tall as it).  {cmd:pipe} and
    {cmd:|} are a vertical bar, turned further by {cmd:msangle()};
    {cmd:point} and {cmd:p} a one-pixel dot whatever {cmd:msize()} says,
    in {cmd:msymbol()} and in a scheme's symbol cycle alike;
    {cmd:V} and {cmd:v} an open chevron; {cmd:arrow} and {cmd:a} draw an
    open triangle and {cmd:arrowf} and {cmd:A} a filled one, as tall as
    the circle (twoway draws an arrowhead on a shaft).
    The cycle reaches every marker: {cmd:scatter}, {cmd:connected},
    {cmd:dot}, {cmd:rconnected}, {cmd:scatteri}, {cmd:rscatter},
    {cmd:pcscatter}, {cmd:pccapsym} and the markers of {cmd:dropline} and
    {cmd:rcapsym}.  A histogram is drawn in the scheme's histogram style,
    {cmd:color histogram} at {cmd:intensity histogram} outlined in
    {cmd:color histogram_line} at {cmd:linewidth histogram}, the same for
    every histogram layer, as {cmd:twoway} draws it; {cmd:color()},
    {cmd:lcolor()} and the fill colour and intensity options still win.
    Plots are numbered as {cmd:twoway} numbers
    them: a {cmd:lfitci}, {cmd:qfitci}, {cmd:lpolyci} or {cmd:fpfitci}
    draws two plots, its band and its line, so
    {cmd:lfitci} || {cmd:lfitci} || {cmd:lfit} draws its lines in
    {cmd:p1}, {cmd:p3} and {cmd:p5}, as {cmd:twoway} does.{p_end}

{phang2}{ul:Named styles.}  {cmd:pstyle()} and {cmd:p()} take
    {cmd:ci}, {cmd:ci2}, {cmd:histogram} and the {cmd:p}{it:#}{cmd:line},
    {cmd:p}{it:#}{cmd:bar}, {cmd:p}{it:#}{cmd:area},
    {cmd:p}{it:#}{cmd:box}, {cmd:p}{it:#}{cmd:dot} and
    {cmd:p}{it:#}{cmd:arrow} series styles; {cmd:mstyle()} takes
    {cmd:ci}, {cmd:ci2}, {cmd:histogram}, {cmd:none},
    {cmd:p}{it:#}{cmd:box}, {cmd:p}{it:#}{cmd:dot} and
    {cmd:p}{it:#}{cmd:arrow}; {cmd:astyle()} and {cmd:bstyle()} take
    {cmd:background}, {cmd:foreground}, {cmd:ci}, {cmd:ci2},
    {cmd:histogram}, {cmd:none}, {cmd:p}{it:#}{cmd:area},
    {cmd:p}{it:#}{cmd:bar} and {cmd:p}{it:#}{cmd:box}; and
    {cmd:lstyle()}, {cmd:clstyle()}, {cmd:mlstyle()}, {cmd:alstyle()} and
    {cmd:blstyle()} take every one of Stata's 76 line styles
    ({cmd:refline}, {cmd:grid}, {cmd:major_grid}, {cmd:foreground},
    {cmd:xyline}, {cmd:none}, {cmd:p}{it:#}{cmd:line} and the rest).
    Each is drawn as {cmd:twoway} draws it, through the scheme's own keys
    along Stata's {cmd:p}{it:#}{it:stub} chain, so a scheme of your own
    that includes a shipped one and sets, say, {cmd:color refline} reaches
    {cmd:lstyle(refline)}; a key your scheme does not reach at all is
    drawn at {cmd:s2color}'s value with the note
    {cmd:(note: dash: color refline not found in scheme, default attributes used -- s2color's value)}.
    A name {cmd:twoway} does not know draws {cmd:twoway}'s default
    attributes -- {cmd:p1} for a series or marker style, the scheme's
    foreground line for a line style and its background area for an area
    style -- with
    {cmd:(note: dash: named style} {it:name} {cmd:not found in class} {it:class}{cmd:, default attributes used)}
    once.  A style name -- {cmd:lstyle(refline)}, {cmd:pstyle(fpall)}, your
    own {cmd:lstyle(mine)} -- is looked up as Stata looks it up: a
    {cmd:linestyle}, {cmd:areastyle}, {cmd:markerstyle}, {cmd:seriesstyle}
    or {cmd:shadestyle} directive in the scheme first, then the
    {cmd:style/<class>-<name>.style} file in your ado-path's style
    directories, with the same size and location checks as a scheme file.
    So every name of Stata's 161 style files ({cmd:fpall},
    {cmd:dendrogram}, {cmd:sunflower}, {cmd:star}, {cmd:refmarker},
    {cmd:plotregion}, {cmd:outline}, {cmd:legend} and the rest) and a
    package's or your own {cmd:linestyle-mine.style} draw their file's
    attributes, and a scheme's {cmd:linestyle ci mine} redefines what
    {cmd:pstyle(ci)}'s line draws.  A directive on a plot's own style is
    drawn as well: {cmd:linestyle p1line mine} a line plot's line,
    {cmd:linestyle p1 mine} the connecting line of {cmd:connected} and the
    other series (not a line plot's, which Stata's schemes declare as
    {cmd:p1line}), {cmd:shadestyle p1area mine} an area's fill.  Each directory is searched before its
    {cmd:style/} subdirectory, as {cmd:findfile} searches.  The rows are
    read when the graph is registered and travel with the dashboard, with
    what Stata's own scheme files declare that {cmd:dash}'s copies do not
    (such as {cmd:s2color}'s {cmd:linestyle p1line}), so {cmd:dash serve}
    on a machine without Stata's files draws the same page.  A style file that is a link out of its directory, or larger
    than 1,048,576 bytes, is not read: it is named in a note and the
    defaults are drawn.  Stata 19.5 has no {cmd:adoarchive} value in
    {cmd:creturn} ({cmd:r(133)}); were style files read from a compressed ado archive,
    {cmd:dash} would say {cmd:(note: dash: style files inside a compressed ado archive are not read; dash's transcribed styles are drawn)}.
    Where no style file can be found (a renderer run without Stata's
    ado-path) a name Stata knows outside the lists above draws the same
    defaults, with
    {cmd:(note: dash: named style} {it:name} {cmd:of class} {it:class} {cmd:is not drawn by dash; default attributes used)}.
    The {cmd:textboxstyle} and {cmd:color} style files are not read, so
    one of your own draws the default where {cmd:twoway} draws the file.
    With a {cmd:color-mine.style} on the ado-path, {cmd:twoway} draws
    {cmd:mcolor(mine)} in its colour; {cmd:dash} draws black markers, with
    {cmd:(note:  dash: named style mine not found in class color, default attributes used)}.
    With a {cmd:textboxstyle-mine.style}, {cmd:twoway} draws
    {cmd:title("T", tstyle(mine))} and {cmd:mlabtextstyle(mine)} in the
    file's size and colour; {cmd:dash} draws the title in its default
    style, with
    {cmd:(note: dash: named style mine not found in class textboxstyle, default attributes used)},
    and the labels in the body text style, with
    {cmd:(note: dash: mlabtextstyle(mine) is not a recognised text style; using the body text style.)}.

{phang2}{ul:Grids.}  A major grid is drawn on an axis only where the
    scheme says so ({cmd:yesno draw_major_hgrid} for the x axis,
    {cmd:draw_major_vgrid} for the y axis), in {cmd:color major_grid} at
    {cmd:linewidth major_grid}; a minor grid only where
    {cmd:draw_minor_hgrid} or {cmd:draw_minor_vgrid} says so, which no
    shipped scheme does.  So {cmd:s1color}, {cmd:s1mono}, {cmd:s1rcolor}
    and {cmd:stmono1} draw no grid at all, as in Stata.  A grid that
    {cmd:xlabel(, grid)} or {cmd:ylabel(, grid)} turns on is drawn in the
    scheme's grid colour and in its {cmd:linepattern major_grid}
    ({cmd:linepattern minor_grid} for a minor grid): the {cmd:st*} schemes
    that dash their grid ({cmd:stcolor} among them) draw it dashed, and
    {cmd:xlabel(, grid)} keeps the dashes.  Ticks are the scheme's:
    {cmd:gsize tick} long in Stata units ({cmd:tiny}, about 5 pixels at
    the 4-inch reference, in whole pixels), on the side
    {cmd:tickposition axis_tick} gives, in {cmd:color tick} at
    {cmd:linewidth tick}.  An axis whose {cmd:axisstyle} draws no line or
    no ticks draws none, and {cmd:yesno alt_yaxes} puts the y axis on the
    right: under {cmd:economist} the y axis is on the right with neither
    line nor ticks, its x ticks point inward, and a {cmd:yaxis(2)} axis
    is on the left with its line and ticks.  An axis with its default
    labels draws no minor ticks, as Stata draws them only when
    {cmd:xmtick()}, {cmd:xmlabel()} or their {it:y} twins ask for them,
    a date axis's default labels included.{p_end}

{phang2}{ul:Text.}  Each piece of text takes the size and colour of the
    Stata textbox style that draws it: {cmd:title()} is {cmd:heading},
    {cmd:subtitle()} is {cmd:subheading}, {cmd:caption()} is {cmd:body},
    {cmd:note()} is the scheme's {cmd:textboxstyle note} -- {cmd:small_body}
    in most schemes, {cmd:key_label} in {cmd:s1manual}, and in
    {cmd:economist} {cmd:reverse_big}, white {cmd:medlarge} text in a box
    filled with {cmd:color reverse_big} (Stata's note textbox does not use
    {cmd:gsize note}, and neither does {cmd:dash}), axis titles are
    {cmd:axis_title}, tick labels {cmd:tick_label} and legend entries
    {cmd:key_label}.  Marker labels take {cmd:color p}{it:#}{cmd:label}
    and {cmd:gsize p}{it:#}{cmd:label} (else {cmd:plabel}, else the plot's
    colour) -- not {cmd:color label} or {cmd:gsize label}, which
    {cmd:twoway}'s marker labels do not read -- and the colour bar's labels
    and title take {cmd:tick_label} and {cmd:axis_title}.  The dashboard's
    own title and subtitle use
    {cmd:heading} and {cmd:subheading}.  Under {cmd:s1rcolor} every one of
    them is white on black; under {cmd:economist} the title is drawn
    larger than the subtitle, as its {cmd:gsize heading 6.0} asks.  No
    title is bold and axis titles are upright.  The title, subtitle, note
    and caption are placed by the scheme's {cmd:clockdir title_position},
    {cmd:subtitle_position}, {cmd:note_position} and
    {cmd:caption_position} and the justification of their boxes
    ({cmd:horizontal heading}, {cmd:subheading}, {cmd:small_body} and
    {cmd:body}): under {cmd:s2color} the title and subtitle are centred
    above the plot and the note and caption at the left below it, the note
    nearer the plot; under {cmd:economist} the title, subtitle and caption
    are at the left and the note sits in its box in the title's band, at
    the top right.  Clock positions 2 to 4 and 8 to 10, which only a scheme
    of your own can ask for, are drawn on the nearer of the top and
    bottom.  The files also carry {cmd:system naturally_white} and the
    {cmd:intensity p}{it:#}{cmd:bar}/{cmd:p}{it:#}{cmd:area} chains as
    Stata resolves them.{p_end}

{phang2}{ul:Legend.}  Its background and border ({cmd:color legend},
    {cmd:color legend_line}), its text ({cmd:key_label}), its placement
    when the graph gives no {cmd:legend(position())}
    ({cmd:clockdir legend_position}) and its ring when it gives no
    {cmd:legend(ring())} ({cmd:gridringstyle legend_ring}), and its
    columns whatever the position ({cmd:numstyle legend_cols}): below the
    plot in two columns under {cmd:s2color}, to the right in one under
    {cmd:stcolor}, above in three under {cmd:economist}.
    {cmd:legend(cols())} and {cmd:legend(rows())} still win, and
    {cmd:legend(rows())} wins over {cmd:legend(cols())}.  Its key
    geometry ({cmd:gsize legend_key_xsize}, {cmd:legend_key_ysize},
    {cmd:legend_key_gap}, {cmd:legend_row_gap}), its inner and outer
    margins ({cmd:margin legend}, {cmd:margin legend_boxmargin}) and
    {cmd:yesno legend_col_first}; {cmd:yesno legend_span} is
    {cmd:legend(span)}'s default; {cmd:gsize legend_col_gap} is carried
    and read, not drawn.{p_end}

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
ladder: a {cmd:large} marker is 7 point against {cmd:medium}'s 4.4.
Every marker, text and gap size dash reads, from an option or from the
scheme, is on one unit for every class: 2.88 point, 3.84 pixels, so the
default marker is 5.87 pixels under {cmd:s2color}.  An option reads a
number, the {cmd:symbolsize} and {cmd:gsize} keywords (case-sensitive,
{cmd:vhuge} and {cmd:ehuge} included for markers), {it:#}{cmd:rs},
{cmd:*}{it:#} (times the size drawn there otherwise) and
{it:#}{cmd:pt}, {it:#}{cmd:in} and {it:#}{cmd:cm}, which are converted at
the scheme's smaller {cmd:graphsize} side ({cmd:xsize()} and {cmd:ysize()}
do not change it).  An unknown or wrong-case name draws the class's
{cmd:medium} with a note, as in {cmd:twoway}; a marker draws the scheme's
own default size ({cmd:large} under {cmd:economist}).  A negative size
draws nothing.  A
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
{ul:A scheme of your own.}  A scheme {cmd:dash} does not ship is found
along the ado-path as {cmd:twoway} finds it:
{cmd:scheme-}{it:name}{cmd:.scheme}, then
{it:name}{cmd:.scheme}, in each directory of the ado-path in turn
({cmd:BASE}, {cmd:SITE}, the working directory, {cmd:PERSONAL},
{cmd:PLUS}, {cmd:OLDPLACE}, directories added with {cmd:adopath}), each
with its first-letter subdirectory, as {cmd:findfile} looks.  So
{cmd:scheme(mytheme)} reads {cmd:scheme-mytheme.scheme} or
{cmd:mytheme.scheme} in the working directory, a third-party scheme
installed into {cmd:PLUS/s/} is read from there, and
{cmd:scheme(mytheme.scheme)} names the file itself.  This holds on every
entry point -- a plot drawn at once with {cmd:dash} {it:plottype}, a
{cmd:scheme()} written on a registered graph or inside a layer's
parentheses, {cmd:dash build}, {cmd:dash serve} and the session's
{cmd:c(scheme)}.  The twenty-six shipped names come first, as Stata's own
are in {cmd:BASE}, so a working-directory {cmd:s2color.scheme} or
{cmd:scheme-s2color.scheme} replaces nothing.  A shipped name may be given
with the extension too, {cmd:scheme(s2color.scheme)}.  A {cmd:theme()}
name given to {cmd:scheme()} is a file of that name when Stata finds one,
and the theme otherwise.  Four things differ from {cmd:twoway}, for
safety: a scheme is a name, never a path (a name holding a blank, a
quote, a slash or backslash, a colon or {cmd:..} is refused, where
{cmd:twoway} follows a relative path); a file is read only when it is a
regular file of at most 1,048,576 bytes inside the directory it was found
in, so a link out of that directory is not followed; a
{cmd:dash-}{it:name} is read only from the working directory; and a file
is read as data, never run.  A file refused this way is named in a note
and {cmd:s2color} is drawn.  The file is read the
way Stata reads it: each line is {cmd:styletype element style}, with the
style the third word, quoted when it holds blanks, as in
{cmd:color background "255 0 0"} or {cmd:color p1 "26 71 111 %20"}.  A
line that cannot be read that way is named once, with its line number,
and skipped.

{pstd}
{ul:A name that resolves to nothing is refused.}  A {cmd:scheme()} that
is neither a shipped scheme, a {cmd:theme()} name nor a scheme Stata
finds is refused before any Python
runs, on every entry point, with r(198):

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang3}{cmd:. dash build, saving(d.html) scheme(nosuchthing) replace}{p_end}
{phang3}{cmd:dash build: scheme() must be one of economist, meta, s1color, s1manual, s1mono, s1rcolor, s2color, s2color8, s2gcolor, s2gmanual, s2manual, s2mono, sj, stcolor, stcolor_alt, stcolor_meta, stcolor_mv, stcoloralias, stgcolor, stgcolor_alt, stgcolor_meta, stgcolor_mv, stmono1, stmono2, stsj, sttrans; a theme (clean, dark, default, economist, mono, sj); or a scheme Stata finds along the ado-path as scheme-NAME.scheme or NAME.scheme (got: nosuchthing)}{p_end}

{pstd}
and a {cmd:theme()} likewise, naming its six values:
{cmd:dash build: theme() must be one of clean, dark, default, economist, mono, sj (got: nosuchtheme)}.
That is stricter than {cmd:twoway}, which draws {cmd:s2color} with a note
when a scheme is not found, and the same as {cmd:set scheme}, which is
r(111): a dashboard is a file you look at later, so {cmd:dash} will not
save one in a scheme you did not ask for.  The session's own
{cmd:c(scheme)}, inherited when you name none, is looked up the same
way, so a scheme {cmd:set scheme} accepted is drawn; it is never refused,
and when {cmd:dash} cannot read it -- a file the rules above refuse -- a
note says why and {cmd:s2color} is drawn.

{pstd}
{ul:What a scheme file of yours may include.}  A colour in your file
follows the grammar of {help dash##colours:Colours}, with {cmd:twoway}'s
scheme-file rules: commas separate the numbers, a malformed number is
drawn white, an unknown name is drawn black with a note, and
{cmd:system naturally_white 0} makes {it:colour}{cmd:*}{it:#} multiply.
StataCorp's schemes are
written as edits on top of an {cmd:#include}d parent, and {cmd:dash}
resolves that chain once, when it extracts its twenty-six translations, so
each shipped file already carries every directive it needs with every
colour written as hex.  A file of yours is read the same way: an
{cmd:#include} is resolved as {cmd:scheme()} itself is -- one of the
twenty-six translations, or {cmd:scheme-}{it:name}{cmd:.scheme} then
{it:name}{cmd:.scheme} along the ado-path.  As in Stata, an {cmd:#include}
takes effect where it stands: the lines after it override the included
scheme, and the included scheme overrides the lines before it.  An
{cmd:#include} that resolves to neither (a scheme nowhere on the
ado-path, or a path) is read as {cmd:#include s2color}, as
Stata reads a scheme it cannot find, and {cmd:dash} says so in Stata's
words, {cmd:(note: scheme} {it:name} {cmd:not found, using s2color)}.
A {cmd:color p}{it:#} or {cmd:linepattern p}{it:#} of yours reaches the
markers, bars and lines of that plot wherever the included scheme
declares nothing more specific, and a {cmd:symbol p} or {cmd:symbolsize p}
reaches every plot whose {cmd:symbol p}{it:#} or {cmd:symbolsize p}{it:#}
the included scheme does not declare (all fifteen under the colour
schemes; none of the symbols under the monochrome ones, which declare
{cmd:symbol p1} to {cmd:p15}, as in Stata), following Stata's
{cmd:p}{it:#}{it:stub} -> {cmd:p}{it:stub} -> {cmd:p}{it:#} -> {cmd:p}
chain.  A {cmd:linewidth p}{it:#} of yours widens plot {it:#}'s line -- a
line, fit, spike, cap, arrow, connecting line or area outline -- by the
same chain, whose stub is the plot type's: {cmd:lineplot} for a line, a
fit, {cmd:kdensity}, {cmd:function} and {cmd:rline}, {cmd:area} for an
area outline, {cmd:arrowline} for {cmd:pcarrow}; a bar's outline stops at
{cmd:linewidth pbar}, which every Stata scheme sets, so {cmd:p}{it:#}
never reaches it, as in Stata; a marker's outline takes the stub
{cmd:mark}.  Only {cmd:graphsize x} and {cmd:graphsize y} size a graph; a bare
{cmd:graphsize} {it:#} sizes nothing, as in Stata.
A directive {cmd:dash} does not draw yet -- such as {cmd:clockdir p}
(where marker labels sit) or the {cmd:textboxstyle} of a title -- is read
and kept with the scheme, without a note, so a later {cmd:dash} that draws
it takes it from your file.
Colours may be Stata colour names or {cmd:#rrggbb}.

{pstd}
{ul:What the shipped files are.}  Each is a translation in {cmd:dash}'s
own format, not a copy of StataCorp's file and not a drop-in Stata
scheme: 310 to 390 directives (more for the monochrome schemes, whose
chains declare connecting-line and line-plot keys, a symbol cycle and
{cmd:color plabel}; every file carries {cmd:gsize plabel}) where Stata's
{cmd:scheme-s2color.scheme}
has 2060, the {cmd:#include} chain flattened into the file, every colour
resolved to {cmd:#rrggbb} ({cmd:sttrans}'s with the {cmd:%20} opacity
Stata declares kept as {cmd:#rrggbb%20}, and {cmd:economist}'s plot-region
border, and the {cmd:pieline} and {cmd:fpspacer} line colours, written as
Stata's {cmd:none}), and a {cmd:* provenance:}
comment for every
directive saying whether it was transcribed from Stata's file, and from
which directive, or inferred by {cmd:dash} where Stata resolves the key
through a fallback and {cmd:dash} writes it out resolved.  The
{cmd:p}{it:#}{cmd:line}, {cmd:p}{it:#}{cmd:bar},
{cmd:p}{it:#}{cmd:markfill}, {cmd:p}{it:#}{cmd:markline} and
{cmd:p}{it:#}{cmd:lineplot} colours, the
line patterns, the marker symbols and the marker sizes are not written
out: each file carries only the keys
Stata's own chain declares, and {cmd:dash} follows the
{cmd:p}{it:#}{it:stub} fallback itself, as Stata does.  Most of the
directives {cmd:dash} does not carry govern what it does not draw: the styling of {cmd:graph bar}, {cmd:box}, {cmd:pie},
{cmd:dot} and {cmd:matrix} charts, and margins (the line styles of those
names, such as {cmd:tick} and {cmd:pie}, are carried for {cmd:lstyle()}).
Some govern
what it draws in its own way, so those can look different from Stata's.
A confidence band's keys are carried -- {cmd:color ci_area},
{cmd:ci_arealine} and {cmd:ci_line}, {cmd:intensity ci_area},
{cmd:linewidth ci_area} and {cmd:ci}, {cmd:linepattern ci_area} and
{cmd:ci}, and {cmd:ci2}'s colours and width -- and drawn as Stata draws
them (see {help dash##ciband:The band's look}), and so are a histogram's:
{cmd:color histogram} and {cmd:histogram_line}, {cmd:intensity histogram}
and {cmd:linewidth histogram}; and so are the keys Stata's style files
read for the named styles, {cmd:color refline} among them.  The shipped
schemes declare {cmd:color plabel}, {cmd:color pline},
{cmd:color plineplot}, {cmd:linewidth p}{it:#}{cmd:solid} and
{cmd:linewidth parea}, which Stata's own files declare too; no drawing
reads them.  A histogram draws the {cmd:%}{it:#} opacity a scheme's
{cmd:color histogram} carries, as twoway does.  {cmd:graph} never reads
these files (see below).

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash build, saving(d.html) scheme(s1rcolor) replace}{p_end}

{pstd}
{ul:Where the shipped schemes live after an install.}  {cmd:dash} ships
its twenty-six schemes as {cmd:dash-}{it:name}{cmd:.scheme} files beside
{cmd:dash.ado}, and {cmd:net install} files each by its first letter, so
all twenty-six land in {cmd:PLUS/d/} -- {cmd:PLUS/d/dash-s2color.scheme},
{cmd:PLUS/d/dash-economist.scheme} and so on -- while
{cmd:dash_render.py} goes to {cmd:PLUS/py/}.  {cmd:dash} looks there for
its own twenty-six names; a name it does not ship is looked for along the
ado-path as Stata looks for it, so another package's file in the same
directory is read only when you name it.  So {cmd:scheme()} works the
same from an installed copy as from a source checkout.  You still name
them as before: {cmd:scheme(s2color)} or {cmd:scheme(s2color.scheme)}.  A
{cmd:.scheme} file in the working directory no longer wins over the
shipped one of the same name, as it never does in {cmd:twoway}.

{pstd}
{ul:Why they are named {cmd:dash-}{it:name}{cmd:.scheme}.}  The
{cmd:dash-} prefix means the files cannot collide with Stata's own
{cmd:scheme-}{it:name}{cmd:.scheme} files or with another package's
{it:name}{cmd:.scheme}, so {cmd:set scheme} {it:name} still finds Stata's
own copy and {cmd:dash}'s translations never change how {cmd:graph} draws
by default.  They are {cmd:dash}'s alone: {cmd:set scheme} {it:name}
finds Stata's own {cmd:scheme-}{it:name}{cmd:.scheme} in {cmd:BASE}
first, so it never reads them, and in
{cmd:dash} you name each by Stata's own name, {cmd:scheme(s2color)},
never by its file name.  In {cmd:dash},
{cmd:scheme(dash-}{it:name}{cmd:)} is not another spelling of a shipped
scheme: it names your own {cmd:dash-}{it:name}{cmd:.scheme} in the working
directory, and is refused when there is none.


{marker unsupported}
{title:Unsupported Stata twoway options}

{pstd}
The options below are {it:accepted and not honoured}.  None of them given
once is an error (given twice, one {cmd:twoway} takes once is refused as
{cmd:twoway} refuses it, as {it:Differences from twoway} says), so a
command copy-pasted from a do-file always runs -- every one that is
supplied and not drawn is named in that command's note, and an option
{cmd:twoway} refuses on a plot type is refused as {cmd:twoway} refuses it
({cmd:r(198)}, {cmd:option X() not allowed}):

{p 12 12 2}{cmd:. sysuse auto, clear}{p_end}
{p 12 12 2}{cmd:. dash scatter mpg weight, afcolor(red) afintensity(50)}{p_end}
{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): afcolor() afintensity())}{p_end}

{pstd}
The note is built from the declarations in {cmd:dash.ado} and from what
its parsers leave over, and this list is checked against both: the
declarations, and the {cmd:twoway} options measured reaching the note
({cmd:test/fixtures/catchall_options_truth.json}, written by
{cmd:scripts/extract_catchall_options_truth.do});
{cmd:test/test_help_conformance.py} fails if the list and either disagree
in either direction.

{phang2}{ul:A confidence band's outline, on other plots.}
    {opt acolor(color)}, {opt alcolor(color)}, {opt alwidth(linewidth)},
    {opt alpattern(linepattern)} -- {cmd:twoway}'s fitarea options.
    {cmd:dash} draws them on the band of {cmd:lfitci}, {cmd:qfitci},
    {cmd:lpolyci} and {cmd:fpfitci}, and does not name them there;
    {cmd:twoway} accepts them on every plot type.  On {cmd:area},
    {cmd:bar}, {cmd:rarea}, {cmd:rbar} and {cmd:histogram} it draws
    {cmd:acolor()} as {cmd:color()} -- the fill, which {cmd:fcolor()}
    still sets, and the outline -- and on the line and paired types
    ({cmd:spike}, {cmd:dropline}, {cmd:tsrline}, {cmd:rspike},
    {cmd:rcap}, {cmd:rline}, {cmd:rconnected}, {cmd:rcapsym},
    {cmd:rpcap}, {cmd:rpspike} and the {cmd:pc} types) as the line's
    colour; {cmd:alcolor()}, {cmd:alwidth()} and {cmd:alpattern()} as
    {cmd:lcolor()}, {cmd:lwidth()} and {cmd:lpattern()}; each over the
    plain option, whatever the order they are typed in, and {cmd:dash}
    draws them so.  On {cmd:scatter}, {cmd:line}, the fits without a band
    and the other types where {cmd:twoway} draws nothing different with
    them, {cmd:contour} and {cmd:contourline} among them, {cmd:dash} takes
    them in silence; {cmd:alpattern()} on {cmd:contour}, which
    {cmd:twoway} draws, it names.

{phang2}{ul:Area, bar and line edge styles.}
    {opt afcolor(color)}, {opt afintensity(intensity)},
    {opt alalign(linealignmentstyle)} -- the rest of {cmd:twoway}'s
    area-style options; {opt bcolor(color)}, {opt bfintensity(intensity)},
    {opt blalign(linealignmentstyle)}, {opt blpattern(linepattern)},
    {opt blwidth(linewidth)} -- its bar-style options; and
    {opt clalign(linealignmentstyle)}, a connecting line's alignment.
    {cmd:twoway} takes them on every plot type; {cmd:dash} draws a fill and
    an outline from {cmd:color()}, {cmd:fcolor()}, {cmd:lcolor()},
    {cmd:lwidth()} and {cmd:lpattern()}, and names these.

{phang2}{ul:Back markers.}
    {opt bmcolor(color)}, {opt bmlalign(linealignmentstyle)},
    {opt bmlcolor(color)}, {opt bmlpattern(linepattern)},
    {opt bmlwidth(linewidth)}, {opt bmsize(markersizestyle)},
    {opt bmsymbol(symbolstyle)} and its other spelling
    {opt bsymbol(symbolstyle)} -- {cmd:twoway}'s back-marker style, taken
    on every plot type; {cmd:dash} draws no back marker, and names them.

{phang2}{ul:Older spellings.}
    {opt msymangle(anglestyle)} and
    {opt mlabels(varname)} -- spellings {cmd:twoway} also takes for
    {cmd:msangle()} and {cmd:mlabel()}.  {cmd:dash} takes
    the names in this file, draws the default for these, and names them.
    (The older spelling symbol, s at its shortest, is read as
    {cmd:msymbol()}, as {cmd:twoway} reads it.)

{phang2}{ul:Marker-label text layout.}
    {opt mlabalignment(alignmentstyle)},
    {opt mlabjustification(justificationstyle)} -- the vertical alignment
    and the justification of a marker label's text box; {cmd:dash} draws
    the label at its position, and names them.

{phang2}{ul:Missing values and legend keys.}
    {opt omitallmiss}, {opt omitanymiss}, {opt omitdupmiss},
    {opt omitnothing} -- {cmd:twoway}'s rules for which observations with
    missing values a plot omits; {cmd:dash} omits as its plot types say,
    and names them.  Two of them in one command, in one plot or in two,
    are refused, r(198), as {cmd:twoway} refuses them.  {opt numkeys(#)} -- the number of legend keys a plot
    contributes; {cmd:dash} draws one key per series, and names it.

{phang2}{ul:Bar-family settings.}
    {opt bartype(spanning)}, {opt bargap(#)}, {opt dropto(#)} on
    {cmd:bar} and the other bar-derived types.  {cmd:bargap()} is an option of {cmd:graph bar}:
    {cmd:twoway bar} accepts it and draws nothing different.  {cmd:dash}
    names all three.

{phang2}{ul:A dot plot's line pattern.}
    {opt dlpattern(linepattern)} -- the pattern of the dots' outline on a
    {cmd:dot} plot; {cmd:dash} draws it solid, and names it.

{phang2}{ul:Type-specific options.}
    {opt xlog} and {opt xtransform(exp)} on {cmd:lfit} and the other fits,
    which fit against a transformed {it:x};
    {opt back} and {opt noback} on {cmd:mspline} and {cmd:mband};
    {opt onepanel} on {cmd:tsline} and {cmd:tsrline}; and
    {opt heatlabel}, {opt zvarlabel(string)}, {opt zvarformat(fmt)} on
    {cmd:contour} and {cmd:contourline}.  {cmd:dash} draws each plot as it
    draws it without them, and names them.

{phang2}{ul:Graph-wide settings.}
    {opt below}, {opt copyscheme}, {opt logging},
    {opt nologging}, {opt refscheme}, {opt norefscheme}, {opt rescaling},
    {opt norescaling}, {opt titling} and {opt notitling} -- settings of
    {cmd:twoway}'s graph object with nothing for {cmd:dash} to draw; it
    names them; {cmd:notitling} with a title, subtitle, note or caption is
    refused as {cmd:twoway} refuses it.  {cmd:maxaxes()} is checked as {cmd:twoway} checks it -- a
    value that is no integer, or an axis numbered above it, is refused --
    and is otherwise taken in silence.

{phang2}{ul:Marker back-line style.}
    {opt bmlinestyle(linestyle)} -- a marker's back line; {cmd:dash}
    keeps it, for each y, and does not draw marker back lines; nor does
    {cmd:twoway} draw anything different with it, so it is taken in
    silence.  A name {cmd:twoway} does not know is noted
    as {cmd:twoway} notes it.

{phang2}{ul:A dot's alignment.}
    {opt dlalign(linealignmentstyle)} -- whether the outline of the dots
    of a {cmd:dot} plot is drawn inside, outside or centred on its edge;
    {cmd:dash} draws it centred, and {cmd:twoway} draws the same picture
    with it, so it is taken in silence.

{phang2}{ul:Connection order.}
    {opt sort} and {opt sort(varlist)} on {cmd:scatter}, {cmd:bar},
    {cmd:spike}, {cmd:dropline}, {cmd:dot}, the range types and the
    {cmd:pc} types draw the marks in that order -- the later on top, in
    {it:x}'s order under {cmd:sort} ({it:x2}'s on a {cmd:pc} type), in the
    saved page, the served app and after a move -- as {cmd:twoway} draws
    them, and are not named; on the fits, {cmd:kdensity},
    {cmd:histogram} and {cmd:function} they change nothing and are taken
    in silence.  On {cmd:line}, {cmd:connected}, {cmd:area}, {cmd:rline},
    {cmd:rarea} and {cmd:rconnected}, and on a
    {cmd:scatter} given {cmd:connect()}, they are honoured, and {cmd:tsline} and {cmd:tsrline} join in time order, as
    {cmd:twoway} does, so none of the eight names them (see
    {ul:Join order} under the plot types).  A malformed {cmd:sort()} is
    refused on every type, as {cmd:twoway} refuses it.

{phang2}{ul:Not drawn.}
    {cmd:msize()} on {cmd:rbar} without {cmd:mwidth},
    {cmd:headlabel} on {cmd:pcspike}, {cmd:pccapsym}, {cmd:pcscatter},
    {cmd:pci}, {cmd:rpcap} and {cmd:rpspike}, {cmd:mangle()} and
    {cmd:barbsize()} off the arrow types, {cmd:recast()} on {cmd:dot}
    and {cmd:sort} on the fits, {cmd:kdensity}, {cmd:histogram},
    {cmd:function} and the immediate types are taken in silence, as
    {cmd:twoway} draws nothing different with them.
    Where {cmd:twoway} draws the same picture with an option of this
    list as without it -- measured on every plot type, graph export
    SVG -- {cmd:dash} takes it in silence, as {cmd:twoway} does; it is
    named only where {cmd:twoway} draws something different.  Stata's {cmd:nodraw} is not in
    this list: written on a graph it is honoured, on an immediate render
    and, once the graph is registered, on {cmd:dash build} and
    {cmd:dash serve} alike, by keeping the browser window shut.
    {cmd:dash build}'s own option for that is {cmd:nobrowser}.

{pstd}
Not in this list, because {cmd:dash} honours them: {cmd:twoway}'s
connecting-line options {cmd:clcolor()}, {cmd:clpattern()} and
{cmd:clwidth()} (abbreviated {cmd:clc()}, {cmd:clp()} and {cmd:clw()}),
which style the line of {cmd:line}, {cmd:connected}, {cmd:lfit},
{cmd:qfit}, {cmd:fpfit}, {cmd:lpoly}, {cmd:lowess}, {cmd:mspline},
{cmd:mband}, {cmd:kdensity}, {cmd:function} and {cmd:tsline}, of a
{cmd:scatter} given {cmd:connect()}, and the fit
line of {cmd:lfitci}, {cmd:qfitci}, {cmd:lpolyci} and {cmd:fpfitci}, in
place of {cmd:lcolor()}, {cmd:lpattern()} and {cmd:lwidth()} -- and of
{cmd:color()} -- whatever the order they are typed in, never touching the
markers.  On every other plot type {cmd:twoway} draws nothing different for
them, and neither does {cmd:dash}.  {cmd:clwidth()} takes 0 to 10000 and is
refused outside that range where the line is drawn, as {cmd:twoway} refuses
it.  {cmd:mlabangle()} and {cmd:mlabformat()} are honoured too; see
{help dash##marker_labels:Marker Label Options}.

{pstd}
Some names that reach the note are not {cmd:twoway} options where they were
written, and {cmd:twoway} itself refuses them with {cmd:r(198)}: it spells
{cmd:xreverse} and {cmd:yreverse} as {cmd:xscale(reverse)} and
{cmd:yscale(reverse)}, which {cmd:dash} honours, and {cmd:xalternate} and
{cmd:yalternate} as {cmd:xscale(alt)} and {cmd:yscale(alt)}, which
{cmd:dash} draws;
{cmd:xcommon} and {cmd:ycommon} are options of {cmd:graph combine};
{cmd:margin()} is a sub-option of {cmd:plotregion()}, {cmd:graphregion()}
and the title options, {cmd:region()} of {cmd:legend()}, and {cmd:altaxis}
of a contour plot's {cmd:clegend()}; {cmd:addplot()} belongs to commands
outside {cmd:graph twoway}, such as {cmd:histogram}; and {cmd:lockaspect},
{cmd:zoom()} and {cmd:ddensity} are options of no Stata graph command.
{cmd:mlabfontface()} is refused by {cmd:twoway} on a marker label,
"option(s) fontface() not allowed", r(198), and {cmd:dash} refuses it in
the same words.

{pstd}
{opt title2(string)} and {opt subtitle2(string)} are not {cmd:twoway}
options: {cmd:twoway} refuses them, "option title2() not allowed", r(198),
and so does {cmd:dash}, after the comma, inside a plot's parentheses and
after a {cmd:||} segment's comma alike.  A second {cmd:title()} is not one
of them: {cmd:title("A") title("B")} draws {cmd:B}, the last copy, as
{cmd:twoway} draws it.

{pstd}
Nor are {opt at(varname)}, {opt blabel(...)}, {opt ciopts(...)},
{opt fitopts(...)}, {opt lineopts(...)}, {opt mlabwidth(size)},
{opt filter(varname, ...)} and {opt link(namelist)}:
{cmd:twoway} refuses each on every plot type, "option at() not allowed",
r(198) -- {cmd:blabel()} is {cmd:graph bar}'s, {cmd:ciopts()} belongs to
commands such as {cmd:marginsplot} and {cmd:sts graph}, {cmd:lineopts()}
to others such as {cmd:stcox}'s diagnostic plots, and {cmd:filter()} and
{cmd:link()} to {cmd:dash build} and {cmd:dash serve} -- and so does
{cmd:dash}, naming the word as typed ({cmd:mlabw()}, {cmd:filt()}), and
{cmd:filter()} and {cmd:link()} after the plot groups' comma too; give
those two to {cmd:dash build}.  {cmd:headlabel} is refused the same way
on every plot type but the paired-coordinate ones, {cmd:rpcap} and
{cmd:rpspike}, as {cmd:twoway} refuses it.

{pstd}
{opt play(recordingname)} is looked for as {cmd:twoway} looks for it:
{cmd:.grec} is added to a name whose last part has no {cmd:.}, and the
file is read where the name says -- the working directory, or the path it
gives -- and then in the {cmd:grec} folder of your PERSONAL directory,
nowhere else on the ado-path.  None found is "recording {it:name} not
found in either PERSONAL or working directory", {cmd:r(601)}, and a file
that is not a Graph Recorder file is refused as {cmd:twoway} refuses it,
{cmd:r(198)}, each after every other refusal of the command.  A recording
{cmd:twoway} can read is refused too, {cmd:r(198)}: its Graph Editor
edits are made to {cmd:twoway}'s graph, which a dashboard does not have,
so play it on the graph {cmd:twoway} draws.  {cmd:play()} empty plays
nothing, as in {cmd:twoway}.

{pstd}
Two further notes on the note itself.  It names option {it:names}, never the
values supplied.  And because an unknown option cannot be told apart from a
misspelled supported one, a typo is reported as ignored rather than
rejected: {cmd:titl(x)} abbreviates {cmd:title()} and works, while
{cmd:titel(x)} appears in the note.



{marker dependencies}
{title:Dependencies}

{pstd}
Run {helpb dash_setup} once before using {cmd:dash}.  It checks everything
below and installs what it can -- the Python packages, each at the version
and sha256 hash {cmd:dash_requirements.txt} pins
({help dash_setup##lock:The hash-pinned lock}); a Python you install and
link yourself:

{phang2}{ul:Stata} -- Stata 19 or later; tested on StataNow 19.5 (MP), macOS
    arm64.  Measured on MP only: Stata 19.0, Stata/BE and Stata/SE are
    admitted but have not been run.  On an older Stata, {cmd:dash} and
    {helpb dash_setup} stop before doing anything else with "dash requires
    Stata 19 or later; this is Stata {it:#}", r(9).  The floor is the Stata
    you run, not the version a do-file sets: a do-file that begins
    {cmd:version 16} still runs {cmd:dash} on Stata 19.

{phang2}{ul:Python 3.11+} -- linked to Stata; see {helpb python}.  Both
    test suites pass under Python 3.11, and a Stata session linked to 3.11
    or 3.12 builds and serves dashboards (measured 07oct2026); numpy 2.3 needs
    Python 3.11, so nothing older is supported.

{phang2}{ul:Python packages, required} -- bokeh>=3.8,<3.10, numpy>=2.3,
    pandas>=2.3.  {cmd:dash} was verified on bokeh 3.8 and 3.9 (any patch
    release of either); under a newer bokeh it draws and prints a note, and
    under one older than 3.8 it stops and names {helpb dash_setup}.  Only
    bokeh has a ceiling.

{phang2}{ul:Python packages, optional} -- none.  Every statistical
    layer is computed with numpy: {cmd:lfitci} and {cmd:mspline} no
    longer use scipy, {cmd:lowess} no longer uses statsmodels, and
    {cmd:qfitci} and {cmd:kdensity} use neither.  An installed scipy or
    statsmodels is neither required nor read, and {helpb dash_setup} no
    longer installs them.

{phang2}{ul:jsonio} -- is no longer needed.  {cmd:dash} writes the data
    out itself, through Stata's Python, so every string value -- quotes,
    backticks, dollar signs, control characters, any UTF-8, a strL -- reaches
    the dashboard exactly as Stata holds it.  Text that is not UTF-8, which a
    web page cannot carry, is shown as Stata's ustrfix function shows it, each invalid
    byte as the replacement character, with a note naming the variable or
    label; {cmd:unicode translate} converts such text first.  A binary strL
    is refused, r(198), naming the variable.  Numbers are written column by
    column as binary arrays (little-endian float64, or float32 where every
    value is exactly one), each missing value, {cmd:.a} to {cmd:.z}
    included, read back as missing with its letter kept: a million values
    take about 8 MB, where one JSON object per observation took about 20 MB.
    A data file written by an earlier {cmd:dash} is still read.
    {helpb dash_setup} neither checks nor installs it.

{pstd}
Before it starts, every {cmd:dash} command but {cmd:dash clear} checks that
the Python Stata uses starts (the one {cmd:c(python_exec)} names, or, with
none set, the one Stata finds by itself; a first call that fails is tried
once more), that it is Python 3.11 or later, and that numpy, pandas
and bokeh are installed and import.  If not, it stops with r(198) and one
message naming what is missing, the Python it looked in and
{helpb dash_setup}, and writes nothing; a registration such as
{cmd:dash scatter mpg weight, name(g1)} is refused the same way.  numpy or
pandas older than {helpb dash_setup}'s minimum is named in a note and the
command goes on.  {cmd:dash clear} clears the registry with no Python and
prunes {cmd:dash}'s temporary files with the packages missing.  A dashboard
app run by hand ({cmd:python app.py}, {cmd:bokeh serve}) checks the same and
stops with the same one line.  With no Python set and none Stata can start,
Stata's own message comes first, then {cmd:dash}'s advice, and the command
stops with Stata's return code.

{pstd}
On a Python that the operating system manages (PEP 668: Homebrew's, and
recent Debian, Ubuntu and Arch Linux system Pythons), {cmd:dash_setup}
installs nothing and says so; {cmd:dash_setup, venv(}{it:path}{cmd:)} sets
up a private environment instead and prints the {cmd:python set exec} line
that links Stata to it.  See
{help dash_setup##pep668:Externally managed Pythons}.


{marker author}
{title:Author}

{pstd}
Billy Buchanan{p_end}
{pstd}
{browse "mailto:william@williambuchanan.net":william@williambuchanan.net}{p_end}

{pstd}
To report a problem or ask for a feature, file an issue at
{browse "https://github.com/wbuchanan/dash":https://github.com/wbuchanan/dash}
(the {it:Issues} tab). Say which version of {cmd:dash} and of Stata you
run, give the command that shows the problem, on {cmd:sysuse} data where
you can, and copy the notes or error it printed.{p_end}


{marker alsosee}
{title:Also see}

{psee}
{helpb dash_setup}, {helpb twoway}, {helpb python}
