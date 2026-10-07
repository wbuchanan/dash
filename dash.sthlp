{smcl}
{* *! version 0.1.0  02oct2026}{...}
{viewerjumpto "Syntax"            "dash##syntax"}{...}
{viewerjumpto "Description"       "dash##description"}{...}
{viewerjumpto "Plot types"        "dash##plottypes"}{...}
{viewerjumpto "Differences from twoway" "dash##differences"}{...}
{viewerjumpto "Subcommands"       "dash##subcommands"}{...}
{viewerjumpto "Dashboard Options" "dash##dashboard_options"}{...}
{viewerjumpto "Layout"            "dash##layout"}{...}
{viewerjumpto "Linking and Brushing" "dash##linking"}{...}
{viewerjumpto "The toolbar"       "dash##toolbar"}{...}
{viewerjumpto "Filters"           "dash##filters"}{...}
{viewerjumpto "KPI Cards"         "dash##kpi"}{...}
{viewerjumpto "Server Mode"       "dash##server_mode"}{...}
{viewerjumpto "Temporary files"   "dash##tempfiles"}{...}
{viewerjumpto "Resource limits"   "dash##limits"}{...}
{viewerjumpto "Examples"          "dash##examples"}{...}
{viewerjumpto "Dependencies"      "dash##dependencies"}{...}
{viewerjumpto "Author"            "dash##author"}{...}
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
{cmdab:sav:ing}{cmd:(}{it:filepath} [{cmd:, replace}]{cmd:)}
{cmd:replace}]

{pstd}{ul:Named graph (accumulate for multi-graph dashboard)}{p_end}

{p 8 17 2}
{cmd:dash} {it:plot_specs} {ifin} [{cmd:,} {it:graph_options}
{cmdab:nam:e}{cmd:(}{it:identifier} [{cmd:, replace}]{cmd:)}]

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
{cmd:csv}
{cmdab:nobr:owser}
{cmd:replace}]

{pstd}{ul:Build Bokeh Server app (write .py file, do not block)}{p_end}

{p 8 17 2}
{cmd:dash build} {cmd:,}
{cmdab:sav:ing}{cmd:(}{it:filepath.py}{cmd:)}
{cmd:server}
[{it:other_build_options}]

{pstd}{ul:Launch Bokeh Server (blocking -- press Break to stop)}{p_end}

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
{cmd:dash_setup} [{cmd:,} {it:{help dash_setup##options:setup_options}}]

{pstd}
where {it:plot_specs} = {cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)}
[{cmd:(}{it:plottype varlist} {ifin} {weight} [{cmd:,} {it:options}]{cmd:)} ...]
or equivalently using {cmd:||} separators; {it:plottype} is one of those
listed in {help dash##plottypes:Plot types}.  An {it:if} or {it:in} written
outside the parentheses of the {it:plot_specs} -- after them, or before a
{cmd:||} -- applies to every plot, on top of a plot's own, as in
{cmd:twoway}; in the {cmd:||} form without parentheses a qualifier belongs
to the plot it is written in.  A {it:weight} belongs to a plot, too:
{cmd:[aweight=}{it:varname}{cmd:]}, {cmd:[fweight=}{it:varname}{cmd:]} or
{cmd:[pweight=}{it:varname}{cmd:]}, one variable rather than an expression
on the layers that honour it; see {help dash##weights:Weights}.


{marker description}
{title:Description}

{pstd}
{cmd:dash} accepts the same syntax as {helpb twoway} and produces an
interactive HTML file instead of a static Stata graph window.
The HTML file works offline in any modern browser -- no server, internet
connection, or special software is required.

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
tooltip, filter or download shows it.  Names beginning with {cmd:__dash} are
reserved for every column dash makes -- the qualifier columns
{cmd:__dashq}{it:#}, the join-order columns {cmd:__dashs}{it:#}, the row
identity {cmd:__dash_row__}, and its
marker-label and jitter columns -- and data holding such a variable are
refused with {cmd:r(110)} before anything is exported; every other Stata
name, however dash-like it looks, is read as your data.

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
string-fix columns above are still generated in the data Stata holds in
memory (dropped again before control returns), so a dataset already at
{cmd:c(maxvar)} may fail with {cmd:r(900)}; and a variable named like a
glyph field a plot derives ({cmd:x}, {cmd:y}, {cmd:top}, {cmd:count},
{cmd:density} and the like) draws its own values as a plot variable but is
shadowed by the derived field in {cmd:hover()} and {cmd:mlabel()}.

{pstd}
This help file documents only the features that differ from or extend
{cmd:twoway}.


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
fewer than three observations, {cmd:lpoly} and {cmd:lpolyci} whose smooth
is missing everywhere -- {cmd:dash} draws in silence too, and
{cmd:mspline} and {cmd:mband} on one observation draw that point.  A
one-variable plot of a type that takes a {it:y} and an {it:x} is "too few
variables specified", r(102).

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
bound is present, as {cmd:twoway} draws it ({cmd:rarea} leaves out an
observation missing either bound).  A malformed name in {cmd:sort()} is
refused on every plot type -- {cmd:sort(x*)} is "* invalid name",
r(198) -- and a name that is no usable variable on the plot types that
draw observations: {cmd:sort(nosuch)} on {cmd:line} is "variable nosuch not
found" and "option sort() incorrectly specified", r(198), in {cmd:twoway}'s
words, and so are more than ten names.  The {cmd:sort()} variables are
never written to the dashboard: their order travels as a rank column,
{cmd:__dashs}{it:#}, that no tooltip, filter or download shows.

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
{ul:Synonyms.}  {cmd:dash} also takes shorter names that {cmd:twoway}
refuses, kept so that older {cmd:dash} do-files still run; a do-file that
uses one runs in {cmd:dash} only.  Each name on the right is the plot type
on its left:

{synoptset 16}{...}
{synopt:{cmd:area}}{cmd:ar}, {cmd:are}{p_end}
{synopt:{cmd:bar}}{cmd:ba}{p_end}
{synopt:{cmd:spike}}{cmd:sp}, {cmd:spi}, {cmd:spik}{p_end}
{synopt:{cmd:dropline}}{cmd:dr}, {cmd:dro}, {cmd:drop}, {cmd:dropl},
    {cmd:dropli}, {cmd:droplin}{p_end}
{synopt:{cmd:lfit}}{cmd:lfi}{p_end}
{synopt:{cmd:qfit}}{cmd:qfi}{p_end}
{synopt:{cmd:fpfit}}{cmd:fp}, {cmd:fpf}, {cmd:fpfi}{p_end}
{synopt:{cmd:lowess}}{cmd:low}, {cmd:lowe}, {cmd:lowes}{p_end}
{synopt:{cmd:lpoly}}{cmd:lpo}, {cmd:lpol}{p_end}
{synopt:{cmd:mspline}}{cmd:msp}, {cmd:mspl}, {cmd:mspli}, {cmd:msplin}{p_end}
{synopt:{cmd:kdensity}}{cmd:kde}, {cmd:kden}, {cmd:kdens}, {cmd:kdensi},
    {cmd:kdensit}{p_end}
{synopt:{cmd:tsline}}{cmd:tsl}, {cmd:tsli}, {cmd:tslin}{p_end}
{synopt:{cmd:tsrline}}{cmd:tsrl}, {cmd:tsrli}, {cmd:tsrlin}{p_end}
{p2colreset}{...}

{pstd}
{cmd:dash} also reads a plot type without regard to case: {cmd:SC} and
{cmd:Hist} draw a scatter and a histogram, where {cmd:twoway} refuses both.

{pstd}
{ul:pccapsym.}  {cmd:pccapsym} draws each spike with the same marker at
both ends: the line options style the spike, the marker options the
markers, and {cmd:mlabel()} labels the first point.

{pstd}
{ul:Immediate values.}  {cmd:scatteri}, {cmd:pci} and {cmd:pcarrowi} read
their values as {cmd:twoway} does: {it:#y #x} for {cmd:scatteri} and
{it:#y1 #x1 #y2 #x2} for {cmd:pci} and {cmd:pcarrowi}, each followed by an
optional clock position in parentheses and then an optional label in
quotes.  A missing value -- {cmd:.} or {cmd:.a} to {cmd:.z} -- draws
nothing, and so does a number past the range of the float {cmd:twoway}
stores it as.  {cmd:dash} refuses, with {cmd:r(198)}, a coordinate that is
not a number, a clock position that is not a number from 0 to 12, and a
list with no whole point, segment or arrow; it also refuses a numlist range
such as {cmd:2/2}, which {cmd:twoway} takes and evaluates as a division.
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
{cmd:nothing found where expression expected}, {cmd:r(111)}.

{pstd}
The points are fixed when the graph is registered, as {cmd:twoway}'s
drawing is fixed when its command runs: a later change to the data or to
the estimates does not move them, and neither does a filter on the page,
saved or served.  Evaluating has {cmd:twoway}'s side effects:
{cmd:runiform()} advances the random-number stream as {cmd:twoway} does,
and data holding at least {cmd:n()} observations are marked changed
({cmd:c(changed)}).  Under {cmd:by()}, {cmd:dash} evaluates the expression
once and draws it in every panel, where {cmd:twoway} evaluates it once per
panel; only random draws differ.  A dashboard spec written by hand without
the points is drawn by {cmd:dash} itself, with the same operators and
missing values, {cmd:x}, {cmd:_pi} and ten functions -- {cmd:sin},
{cmd:cos}, {cmd:tan}, {cmd:exp}, {cmd:log}, {cmd:log10}, {cmd:sqrt},
{cmd:abs}, {cmd:floor} and {cmd:ceil}; anything else draws that layer
empty, and a note names it.

{pstd}
{ul:Graphs that need no data.}  A graph whose plots are all
{cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} or {cmd:function} draws from its
own values, and needs no data in memory, as in {cmd:twoway}: it is drawn
without any, and {cmd:dash build} builds a dashboard of such graphs, saved
or served, exporting no variable.  Every other plot type takes variables,
and is refused without them, as {cmd:twoway} refuses it:
{cmd:varlist required}, {cmd:r(100)}.

{pstd}
{ul:Not drawn.}  Five {cmd:twoway} plot types are not drawn by {cmd:dash}:
{cmd:contour} and {cmd:contourline}, which interpolate a surface over a
grid from their three variables; {cmd:heatmap}, which colours the cells of
a grid by {it:z}; and {cmd:rpcap} and {cmd:rpspike}, which mark a point on
a range.  Each is refused with {cmd:r(198)} and a message naming what to
use instead: {cmd:twoway} itself, {cmd:dash scatter} {it:y x}{cmd:,}
{cmd:colorvar(}{it:z}{cmd:)} for the first three, or a range plot and a
{cmd:scatter} of the point in one graph for the last two.  Any other word
that is not a plot type is refused too, and the message lists the plot
types above.  A plot type cannot be handled as an unknown option is --
named in a note and drawn around -- because it is what would be drawn.


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
    {cmd:r(602)}).  Write {cmd:replace} after the comma, as for
    {cmd:dash build}, or {cmd:saving(}{it:filepath}{cmd:, replace)}, as for
    {cmd:twoway}, to write over it.  A directory in the file's place is
    never written: with {cmd:replace} it is refused with {cmd:r(608)}, as
    {cmd:twoway} refuses it, on the one-line form and {cmd:dash build}
    alike.  {cmd:replace} with no {cmd:saving()}, or on a named graph,
    has nothing to replace and is named in the note.

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
    {cmd:yline()} keeps its own style.  An option {cmd:twoway} takes once --
    {cmd:name()}, {cmd:saving()}, {cmd:scheme()}, {cmd:xsize()},
    {cmd:ysize()}, {cmd:aspectratio()}, a bare {cmd:sort},
    {cmd:horizontal}, {cmd:yaxis()}, {cmd:bwidth()} on {cmd:kdensity} --
    given twice is refused as {cmd:twoway} refuses it:
    {cmd:option scheme() not allowed}, {cmd:r(198)}.  So are the options
    {cmd:dash} names in its note that {cmd:twoway} takes once, and a
    kernel written as an option of its own ({cmd:gaussian}):
    {cmd:atobs} on the fits, {cmd:nofit}, {cmd:boundary}, {cmd:nodropbase},
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
    {cmd:dash} accepts every {cmd:twoway} option by name.  An unknown option
    is not an error -- unless it is written in upper case, or is a plot's
    option after the plot groups' comma, which {cmd:twoway} refuses and so
    does {cmd:dash} (see {it:Where a graph-level option may be written}
    under 3. above) -- so a command copy-pasted from a do-file runs whenever
    {cmd:dash} draws its plot type -- {help dash##plottypes:Plot types}
    names the five {cmd:twoway} plot types it refuses -- and can draw the
    values it is given: a few values {cmd:twoway} accepts, such as
    {cmd:yaxis(3)}, are more than {cmd:dash} draws and are refused (see
    {help dash##validation:Option values} below).  Anything {cmd:dash}
    cannot honour is named once per command, in a single note:

{p 12 12 2}{cmd:. sysuse auto, clear}{p_end}
{p 12 12 2}{cmd:. dash scatter mpg weight, play(x) text(20 3000 "hi")}{p_end}
{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): play() text())}{p_end}

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
    The note names option {it:names}, never the values supplied.  Because
    an unknown option cannot be distinguished from a misspelled supported
    one, a typo is reported as ignored rather than rejected: {cmd:titl(x)}
    is abbreviated {cmd:title()} and works, but {cmd:titel(x)} appears in
    the note.  The full list is in
    {help dash##unsupported:Unsupported Stata twoway options}.  One kind
    of option is still dropped without a word: an option {cmd:dash}
    honours on some plot types, given on one that does not take it --
    {cmd:bwidth()}, {cmd:n()}, {cmd:bands()}, {cmd:range()}, {cmd:base()}
    or {cmd:level()} on a {cmd:scatter}, say, where the plot types each
    option applies to are listed under
    {help dash##smoother_options:Statistical Layer Options} -- is ignored,
    where {cmd:twoway} refuses the command with r(198).
    The same holds one level down: a sub-option of {cmd:legend()},
    {cmd:xlabel()}/{cmd:ylabel()}, {cmd:xscale()}/{cmd:yscale()},
    {cmd:xtitle()}/{cmd:ytitle()}, {cmd:title()}, {cmd:subtitle()},
    {cmd:note()}, {cmd:caption()}, {cmd:xline()}/{cmd:yline()} or
    {cmd:filter()} that {cmd:dash} does not implement is named in a
    note, as {cmd:by()}'s are:
    {cmd:(note: dash: legend() sub-option(s) not implemented and ignored: span stack)}.
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
    default with {cmd:twoway}'s note.  {cmd:rows()} wins over
    {cmd:cols()}, and in one copy a word wins over its {cmd:no} form
    ({cmd:on} over {cmd:off}, {cmd:grid} over {cmd:nogrid}).  Repeated
    copies merge sub-option by sub-option under the full name, the last
    copy winning, so {cmd:legend(lab(1 "A")) legend(lab(2 "B"))} keeps
    both labels.
    A textbox sub-option -- of {cmd:title()}, {cmd:subtitle()},
    {cmd:note()}, {cmd:caption()}, {cmd:xtitle()}/{cmd:ytitle()} and
    {cmd:xtitle2()}/{cmd:ytitle2()} -- is read under any of Stata's
    spellings, from its minimum abbreviation to its full name:
    {cmd:c(red)} is {cmd:color(red)}, {cmd:s(large)} is
    {cmd:size(large)}, {cmd:a()} is {cmd:alignment()}, {cmd:lst()} is
    {cmd:lstyle()}, {cmd:b} is {cmd:box} and {cmd:nob} is {cmd:nobox}.  {cmd:size()}, {cmd:color()}, {cmd:prefix},
    {cmd:suffix} and, on an axis title, {cmd:axis(1)}/{cmd:axis(2)}
    (minimum {cmd:ax()}, in lower case) are applied; every other
    sub-option is named, never drawn as text.  A lone {cmd:suffix} on an axis title adds its lines after the
    default title, {cmd:prefix} before it.
    An axis title given with empty text -- {cmd:xtitle("")},
    {cmd:ytitle("")}, {cmd:ytitle("", axis(2))} or {cmd:ytitle2("")} --
    removes that title, as in {cmd:twoway}; an option not given at all
    keeps the default (the variable's label, {cmd:Density},
    {cmd:kdensity} {it:var}).
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
    not; on {cmd:scatter} and the other glyph layers it is named in the
    same note by type and never by variable, as {cmd:[aweight]}.  See
    {help dash##weights:Weights}.
    {cmd:scheme()} is not among the options named: {cmd:dash} translates
    Stata's own schemes; {help dash##scheme:Stata scheme support} below says
    what a scheme sets and what {cmd:dash} does not yet carry.

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

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash (scatter mpg weight, yaxis(3))}{p_end}
{phang3}{cmd:dash: yaxis() must be an integer between 1 and 2 (got: 3). dash draws two axes.}{p_end}

{phang2}    The bounds checked in Stata.  Numbers: {cmd:jitter()} 0 to 100;
    {cmd:malpha()}, {cmd:lalpha()} and {cmd:falpha()} 0 to 100;
    {cmd:level()} strictly between 0 and 100 (on {cmd:lpolyci}, 10 to
    99.99, as {cmd:twoway}); {cmd:aspectratio()} 0 or
    more; {cmd:base()} any number; {cmd:start()} any number, except that
    on {cmd:histogram} a {cmd:start()} above the variable's minimum is
    refused in {cmd:twoway}'s own words,
    {cmd:option start() may not be larger than minimum of mpg};
    {cmd:barwidth()}, {cmd:width()} and {cmd:bwidth()} positive, and on
    {cmd:lowess}
    {cmd:bwidth()} is a fraction of the sample, so at most 1.  Integers:
    {cmd:yaxis()} and {cmd:xaxis()} 1 or 2; {cmd:degree()} 0 to 3;
    {cmd:n()} 2 to 10000, or 1 to 300 on {cmd:mspline}; {cmd:bin()} 1
    to 1000; {cmd:bands()} 1 to 200;
    {cmd:colornlevels()} 2 to 256; {cmd:jitterseed()} and {cmd:jseed()}
    0 or more; an integer written as {cmd:yaxis(2.0)}, {cmd:yaxis(02)},
    {cmd:yaxis(+2)} or {cmd:n(1E3)} reaches the renderer as 2, 2, 2 and
    1000.  A name or a number: {cmd:msize()}, {cmd:mlabsize()},
    {cmd:mlabgap()}, {cmd:mlabposition()} and {cmd:fintensity()} any
    number, and {cmd:msize()}, {cmd:mlabsize()} and {cmd:mlabgap()} also a
    number with a unit ({cmd:4pt}, {cmd:.1in}) or a {cmd:*}{it:#}
    multiplier; {cmd:lwidth()} and {cmd:mlwidth()} 0 to 10000;
    {cmd:alwidth()} 0 to 10000 on the plot types where {cmd:twoway}
    refuses it outside that range (every type but {cmd:line},
    {cmd:connected}, the fits and smooths without a band, {cmd:kdensity},
    {cmd:function}, {cmd:tsline}, {cmd:scatter}, {cmd:dot},
    {cmd:rscatter} and {cmd:scatteri});
    {cmd:msangle()} -360 to 360; {cmd:xsize()} and {cmd:ysize()} 1 to
    100; a word that only looks like a number, such as
    {cmd:msize(1e308)}, is refused as {cmd:twoway} refuses it
    ({cmd:invalid syntax}).  A word
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
    {cmd:by(foreign)}; a variable that does not exist is r(111) ({cmd:dash build}
    and {cmd:dash serve} also give r(111) for a {cmd:hover()} variable
    dropped after the graph was registered), and a
    time-series expression such as {cmd:mlabel(L.mpg)} is refused, as
    {cmd:twoway} refuses it.  {cmd:xsize()},
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
    no second sentence: {cmd:jitter()} 0 to 100, {cmd:level()} strictly
    inside 0 and 100 (on {cmd:lpolyci}, {cmd:twoway}'s words), {cmd:barwidth()} positive, {cmd:aspectratio()} 0 or
    more, {cmd:jitterseed()} 0 or more, and the {cmd:kdensity}
    {cmd:bwidth()} positive ({cmd:kdensity} itself accepts
    {cmd:bwidth(0)}).  {cmd:malpha()}, {cmd:lalpha()}, {cmd:falpha()},
    {cmd:jseed()}, {cmd:colornlevels()}, {cmd:colpalette()} and {cmd:hover()}
    are options {cmd:twoway} does not have, so every rule on them is
    {cmd:dash}'s own.  {cmd:bands()} 1 to 200 is {cmd:twoway}'s own bound
    ({cmd:bands must be between 1 and 200}).

{phang2}    {cmd:dash} also refuses some forms {cmd:twoway} reads:
    {cmd:mlabel()} with more than one variable ({cmd:twoway} labels the
    markers with the first); {cmd:range(}{it:varname}{cmd:)} on
    {cmd:function} and {cmd:kdensity}, and a {cmd:.} for the data's own
    end in {cmd:range()} on {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and
    {cmd:qfitci} ({cmd:dash} takes two numbers); a number too large for
    Stata that {cmd:twoway} lets through, as in {cmd:msize(1e400)}; and a
    width or an angle outside its bounds on a plot type that does not
    draw what it styles.  {cmd:twoway} checks {cmd:lwidth()} only where
    it draws a line or an outline, and {cmd:mlwidth()} and
    {cmd:msangle()} only where it draws markers; {cmd:dash} checks them
    on every plot type, so {cmd:scatter mpg weight, lwidth(-1)}, which
    {cmd:twoway} draws, is refused.

{phang2}    Some values {cmd:twoway} refuses, {cmd:dash} accepts:
    {cmd:kernel(GAUSSIAN)} is read as {cmd:kernel(gaussian)}; a style
    option given an empty pair of parentheses, such as {cmd:lwidth(())},
    {cmd:msize(())} or {cmd:xsize(())} ({cmd:twoway}:
    {cmd:option(s) ( ) not allowed}), passes as a name that the renderer
    then reports; and
    {cmd:colorvar()} takes a string variable, drawn a colour for each
    value, where {cmd:twoway} wants a numeric one.  An unknown
    {cmd:scheme()} is refused where {cmd:twoway} draws {cmd:s2color} with
    a note, because a saved dashboard in the wrong scheme is not a note
    you see, and so is an unknown {cmd:theme()}, an option {cmd:twoway}
    does not have; {help dash##scheme:Stata scheme support} says more.

{phang2}    A switch that belongs to one plot type is refused on every
    other, as {cmd:twoway} refuses it, with r(198): {cmd:discrete} on
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

{phang2}    Colours, {cmd:msymbol()}, {cmd:lpattern()} and the sub-options of
    the structured options are not checked in Stata.  An unknown style
    inside one ({cmd:title(T, size(bogus))}) gets a note and the default
    in {cmd:twoway} and in {cmd:dash} alike.  An unknown sub-option word
    of {cmd:legend()} is refused as {cmd:twoway} refuses it
    ({cmd:legend(garbage)}: {cmd:option garbage not allowed}, r(198));
    one of {cmd:xscale()}, which {cmd:twoway} refuses too
    ({cmd:xscale(bogus)}), {cmd:dash} names in its sub-option note and
    draws without.  A colour written with commas,
    {cmd:mcolor(255,0,0)}, which {cmd:twoway} refuses, {cmd:dash} reads as
    the triplet {cmd:255 0 0}.

{phang2}6.  {ul:Variable and value labels used automatically.}
    {cmd:dash} reads variable labels (they title the axes, key the legend,
    name the tooltip rows and the colour key, and title filter widgets)
    and value labels (for filter dropdowns, the titles of
    {cmd:by()} panels, marker labels, the legend of a discrete
    {cmd:colorvar()} and the CSV download) without any additional options.
    An axis is labelled with numbers, as in {cmd:twoway}, unless its
    {cmd:xlabel()}/{cmd:ylabel()} (or {cmd:xlabel2()}/{cmd:ylabel2()})
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
    {cmd:kdensity} {it:varname}, as in {cmd:twoway}.


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
The server runs in the foreground: Stata waits until you press Break
(Ctrl+C in console Stata), the optional {cmd:timeout()} expires, or Stata
itself exits.  When a filter moves, the
server recomputes, from the rows the filters leave, every layer computed
from the data -- a histogram's bins as well as its bars, a fitted or
smoothed line, a kernel density curve -- and every KPI card that follows
the filters.  A saved dashboard recomputes those cards, its kernel density
curves and its histogram bar heights in the browser, and keeps its other
computed layers, and its histogram bins, as they were built; see
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
{synopt:{cmdab:sav:ing}{cmd:(}{it:filepath}{cmd:)}}required; path to
    the output HTML file, which must end in {cmd:.html}; see
    {help dash##saving_chars:Characters in saving()}{p_end}
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
    {cmd:.py}; does not block or open a browser; see
    {help dash##saving_chars:Characters in saving()}{p_end}
{synopt:{cmdab:nobr:owser}}write the dashboard but do not open it in a
    browser.  Stata's own {cmd:nodraw} on the graph has the same effect, and
    setting the global {cmd:$dash_nobrowser} to any non-empty value suppresses
    the window for a whole session -- for {cmd:dash build}, the one-line
    form and {cmd:dash serve} alike -- useful in batch, where one window per
    {cmd:dash build} is rarely wanted; see
    {help dash##nobrowser_global:The global dash_nobrowser}{p_end}
{synopt:{cmd:replace}}overwrite output file if it already exists{p_end}
{synoptline}

{marker saving_chars}
{pstd}
{ul:Characters in saving().}  A {cmd:saving()} path may not hold a double
quote, a backquote, {cmd:$}, {cmd:;}, {cmd:&}, {cmd:|}, {cmd:<}, {cmd:>} or
a control character such as a tab or a line break, may not have a {cmd:..}
segment, and its file name may not begin with {cmd:-}: such a path is
refused, r(198), and nothing is written.  Other characters, {cmd:%}, {cmd:!}
and {cmd:^} among them, are written as typed, as {cmd:twoway}'s
{cmd:saving()} writes them.  On Windows, dash does not open a page whose
path holds {cmd:%}, {cmd:!}, {cmd:^}, {cmd:&}, {cmd:|}, {cmd:<}, {cmd:>} or
{cmd:;}, because Windows' command shell, through which the page would be
opened, reads them as instructions: the page is written, dash prints its
path, and you open it yourself.  This includes the one-line form's preview
page when the name of your user folder holds such a character.

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
The one-line form has no {cmd:nobrowser} option: written there, it is named
in the note and the window opens; the global, the graph's {cmd:nodraw} or
{cmd:saving()} keeps that window shut.  The global is meant for do-files
run in batch and for test suites, where one window per dashboard is rarely
wanted.


{marker export}
{title:Exporting}

{pstd}
Every dashboard can save its figures as a PNG image, with the save button
on the toolbar (see {help dash##toolbar:The toolbar}).  With {cmd:csv} it
can also give you its data.

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

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash kpi mean(mpg), title("Avg MPG") name(k1)}{p_end}
{phang2}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
{phang2}{cmd:. dash scatter mpg length, name(s2)}{p_end}
{phang2}{cmd:. dash histogram mpg, name(s3)}{p_end}
{phang2}{cmd:. dash build, saving(d.html) tabs(Overview: k1 s1 / Detail: s2 s3) replace}{p_end}

{pstd}
Tab titles are used exactly as written, less the blanks around them; the
first colon ends a title, so a title cannot hold a colon, nor a {cmd:/}.  A
group written without a colon is titled by its place: {cmd:Tab 2} for the
second.  A registered item named in no tab is still drawn, below the tabs.
Names that are not in the registry are ignored without a message, and a tab
left with no registered name is not drawn.  {cmd:tabs()} works with every
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
{cmd:rbar} shows it in neither mode: its bars are drawn from its own rows,
their width from those rows' spacing.

{pstd}
{cmd:link(}{it:name1} {it:name2} [{it:name3} ...]{cmd:)} -- link the
specified graphs.  All graphs must have been registered with {cmd:name()};
a name the registry does not hold is refused with {cmd:r(198)}, and a KPI
card's name is accepted and has no effect.  Only one link group per
dashboard is supported: {cmd:link()} is given once, as Stata's
{cmd:syntax} refuses an option given twice ({cmd:r(198)}).

{pstd}
{cmd:link(_all)} -- link all registered graphs.  {cmd:_all} stands alone:
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
{synopt:Undo}step back through your pans, zooms and box and lasso
    selections.{p_end}
{synopt:Redo}step forward again.{p_end}
{synopt:Reset}return to the view the page opened with, and clear the
    selection and what Undo would step back through.{p_end}
{synopt:Save}write the figures to a PNG image; see below.{p_end}
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
{cmd:g1}.  Your browser decides where the file goes.  The image holds only
the figures: a KPI card in a grid is left blank, and the title, the filters
and the tab strip, which sit outside every grid, are not in it.


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
{cmd:label(}{it:string}{cmd:)}]{cmd:)}

{pstd}
{it:varname} may be abbreviated, as anywhere in Stata, and may hold
Unicode letters, as any Stata name may.  Without {cmd:type()} the widget
is a dropdown.

{phang2}{cmd:type(dropdown)} -- select widget listing every distinct value
    of {it:varname}: a numeric or date variable's values as numbers (a
    missing value is not listed), a string variable's exact text, its empty
    string as a blank row.  Selecting a value keeps the observations equal
    to it -- a number compared as a number, a text compared exactly, so
    {cmd:"01"} and {cmd:"1"} are two values -- in the saved page and the
    served app alike.  A listed value is written in the variable's display
    format, or its value label; values that share one display text are one
    entry that selects them all; and a %tw, %tm, %tq, %th or %ty variable's
    range slider moves over Stata's period numbers in steps of one.
    An "All" option removes the filter.  A dropdown lists at most 1,000
    values: over that, a numeric or date variable is drawn as
    {cmd:type(range)} instead, and a string variable lists its first 1,000
    values in sort order, each with a note (see
    {help dash##limits:Resource limits}).

{phang2}{cmd:type(slider)} -- slider that keeps observations where
    {it:varname} is at or above the slider's value; its title ends in a
    greater-than-or-equal sign.

{phang2}{cmd:type(range)} -- range slider that keeps observations where
    {it:varname} is between the low and high slider values, both included.

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

{phang2}{cmd:label(}{it:string}{cmd:)} -- the text shown beside the widget.
    Without it the variable's own label is used, and failing that its name.
    The text may hold any character -- a semicolon, a {cmd:|} or a
    {cmd:||} included.  Put it in double quotes, or in compound double
    quotes when it holds a double quote, if it holds a parenthesis that is
    not balanced; the quotes are not shown.

{pstd}
{cmd:type()} must be one of the three above; any other value is named in a
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
{cmd:dash kpi} {it:stat}{cmd:(}{it:varname}{cmd:)} {ifin} {cmd:,}
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
{cmd:count} and {cmd:dcount} also take a string variable, and count its
values that are not empty; every other statistic needs a numeric variable
and refuses a string one with {cmd:r(109)}.  Over no observations -- a
filter can leave a card none -- {cmd:count}, {cmd:dcount} and {cmd:sum} are
0 and every other statistic is missing, shown as {cmd:.}, as
{cmd:summarize} has them; {cmd:sd}, {cmd:var}, {cmd:cv} and {cmd:skewness}
of one observation are missing too.  Of a date variable, {cmd:mean},
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


{marker server_mode}
{title:Server Mode}

{pstd}
{cmd:dash serve} runs the dashboard as a Bokeh Server application: it writes
the application into a private temporary folder (see
{help dash##tempfiles:Temporary files and privacy}), runs it with Python and
waits until the server stops.  {cmd:dash build, server} writes the same
application to the file {cmd:saving()} names and returns without starting
it.  The saved page and the served app differ as follows:

{col 5}{it:Feature}{col 38}{it:Saved page}{col 59}{it:Served app}
{col 5}{hline 72}
{col 5}Requires internet / server{col 38}No{col 59}Yes (local)
{col 5}Shared as{col 38}one .html file{col 59}one .py, for Python
{col 5}Filter widgets{col 38}JavaScript{col 59}Python callbacks
{col 5}KPI recomputation on filter{col 38}Yes{col 59}Yes
{col 5}Brush/lasso KPI update{col 38}Yes{col 59}Yes
{col 5}Histogram recompute on filter{col 38}heights; bins marked{col 59}heights and bins
{col 5}Kernel density on filter{col 38}same grid, marked{col 59}grid recomputed
{col 5}Fit-line recompute on filter{col 38}No; marked{col 59}Yes
{col 5}A slider recomputes{col 38}at every step{col 59}when released
{col 5}Dates{col 38}Yes{col 59}Yes
{col 5}Toolbar, save as PNG{col 38}Yes{col 59}Yes
{col 5}{cmd:scheme()}, {cmd:theme()}{col 38}Yes{col 59}Yes
{col 5}{cmd:layout()}, {cmd:tabs()} and{col 38}Yes{col 59}Yes
{col 7}{cmd:filterposition()}
{col 5}Bootstrap {cmd:layout(bs)}{col 38}reflows{col 59}reflows
{col 5}Health endpoint{col 38}n/a{col 59}{cmd:/health}
{col 5}Who can open it{col 38}who has the file{col 59}who has its link
{col 5}Deployment{col 38}email, open file{col 59}{cmd:python app.py}
{col 5}{hline 72}

{pstd}
{ul:What a filter move redraws.}  The saved page draws every layer that
plots observations -- scatter, line, area, bar, spike, dropline, the range
and paired-coordinate plots, and their marker labels -- from the rows that
pass the filter, each from its own rows among them, a line still in its join order
and a bar's or cap's width taken from the spacing of the rows kept.  It
recounts a histogram's
bars, and re-estimates a density on its grid, from the rows that pass the
filter -- for a {cmd:by()} panel, or a graph or plot with its own {cmd:if}
or {cmd:in}, from its own rows among them -- and keeps the bin edges and the
grid chosen when the dashboard was built, so neither moves as you filter; it
does not refit a fitted or smoothed line ({cmd:lfit}, {cmd:qfit},
{cmd:lfitci}, {cmd:qfitci}, {cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess},
{cmd:lpoly}, {cmd:lpolyci}, {cmd:mband}, {cmd:mspline}).  When a move
removes observations such a line, a histogram's bins or a density's grid was
computed from, the page marks the layer: it is dimmed, its legend key reads
"(unfiltered)", "(bins unfiltered)" or "(grid unfiltered)", the graph shows
"Marked layers were computed before the filter", and a note under the
filters says the same in text a screen reader reads.  A density drawn over
{cmd:range()} keeps the grid you gave and is not marked.  The marks go when
the filters again keep every observation the layer was computed from; a move
that removes only observations the layer never used (a missing y, x or
weight, a zero weight, or one outside the plot's own {cmd:if} or {cmd:in})
marks nothing, and a graph {cmd:exclude()} protects is never marked.  The
served app draws every layer again from
the rows that pass the filter -- each layer from its own rows among them --
bins, grid, fitted line and bar widths included.  A plot's own {cmd:if} or {cmd:in}
inside a linked {cmd:by()} panel, or inside a linked graph with its own
{cmd:if} or {cmd:in}, keeps to that panel's or graph's observations after
every move, in both.  In both, a filter move clears a
selection brushed on a graph it redraws, and a card that follows the brush
({cmd:update(brush)} or {cmd:update(both)}) then counts the rows that graph
shows.  In both, a layer that a filter, a {cmd:by()} panel or its own
{cmd:if} or {cmd:in} leaves with no observations keeps its colour, width and
legend key, as twoway draws it.

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
written anyway, and a line beginning {cmd:dash: note:} names it.

{pstd}
If no server starts -- the port is in use, or the app
stops before it answers -- {cmd:dash serve} says why and returns r(198)
instead of blocking.

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
{it:N} described below.  No browser window opens unless {cmd:--show} is
given, so the app is usable from a script or a batch job.

{pstd}
The app never runs without a key, and only a link holding it opens the
dashboard: {cmd:http://127.0.0.1:}{it:N}{cmd:/?token=}{it:key}.  Unless you
choose the key, each start makes a new one, writes that link to a file named
{cmd:link.html}, readable only by you, in a new folder only you can open,
and prints the file's path on a line of its own before the server starts;
the key itself is never printed.  Open the file, or copy the link from it;
the folder is removed when the app stops.  On a disk that keeps no file
permissions the file is written anyway, and a line beginning
{cmd:dash: note:} names it; set {cmd:TMPDIR} to a folder on a disk that
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
{cmd:/health}, none of the headers below is sent, the session limits below
do not apply ({cmd:bokeh serve} runs the script afresh for each session, so
every session starts a new count), and the app's flags above are not read.
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
{cmd:bokeh serve app.py} uses Bokeh's own check, so run it under Bokeh 3.9
or later.

{pstd}
Bokeh's environment variable {cmd:BOKEH_ALLOW_WS_ORIGIN}, when it is set,
replaces that allow-list: Bokeh admits the origins it names {it:instead of}
{cmd:localhost}, {cmd:127.0.0.1} and {cmd:--allow-websocket-origin}.  The
app says so when it starts, naming them, and warns when the variable holds
{cmd:*}: the origin check then admits every website, and only the
dashboard's key keeps another site's page out.  Unset it to have the app's
own list apply.

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
with status 429.  The server logs each refusal -- once a minute per limit,
so a flood cannot flood the log -- naming the limit and, for a session
limit, its flag.  No client that is still active is ever forgotten to make
room for new ones, so a flood of addresses cannot reset a real client's
count.

{pstd}
{ul:Recomputation.}  In the served app a slider recomputes the dashboard
when you release it, not at every step of the drag as on the saved page.
In each browser session, each filter widget and each brushed data source
then recomputes at most 10 times in a burst and twice a second after that;
changes that arrive faster are folded into one recomputation with the
latest values.  A script that moves a widget in a loop is therefore held to
that rate, and the server -- one process, one event loop -- runs one
recomputation at a time for every session together.

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


{marker limits}
{title:Resource limits}

{pstd}
The quantities below decide how much {cmd:dash} builds -- the values it
embeds and the bytes of text among them, the graphs in the registry and the plots in a graph, the panels of
a {cmd:by()} graph, and the tabs, filters and dropdown values a dashboard
draws -- and each has a limit, so that none of them can grow without bound.
Each limit has a default, a ceiling that nothing moves, and a global macro
that moves it for the rest of the session:

{synoptset 28 tabbed}{...}
{synopthdr:global}
{synoptline}
{synopt:{cmd:$dash_max_cells}}values the saved page embeds: for a graph
    that draws rows, or that a {cmd:filter()}, {cmd:link()}, {cmd:csv} or
    {cmd:hover()} reaches, its variables -- the ones its layers plot and
    the ones {cmd:hover()} names when one of its layers can show them --
    and qualifier columns times the observations; for a graph made only of computed layers ({cmd:histogram},
    {cmd:kdensity}, a fit or a smoother) that nothing else reaches, the
    values its layers draw, not one row per observation; KPI cards and
    {cmd:filter()} variables always count.  A served app embeds every
    observation of every variable it uses, whatever the graphs; default
    5,000,000, at most 20,000,000.  Over it the build is refused with
    {cmd:r(134)} before anything is exported, naming the count.{p_end}
{synopt:{cmd:$dash_max_bytes}}bytes of text embedded: the length in bytes
    of every string value, {cmd:strL} values included, of the string
    variables a dashboard uses, as Stata stores them; default 50,000,000,
    at most 500,000,000.  Over it the dashboard is refused with
    {cmd:r(134)} before anything is exported.  On the saved page a string
    variable {cmd:hover()} names counts under the same rule as for
    {cmd:$dash_max_cells} (when a layer of its graph can show it, or
    {cmd:csv} is given); a served app counts every string variable it
    exports.  Numbers are counted by {cmd:$dash_max_cells} alone.{p_end}
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
{synopt:{cmd:$dash_max_by_groups}}groups one {cmd:by()} graph draws, a panel
    each, and its {cmd:total} panel one more; default 100, at most 1,000.
    The first groups in sort order are drawn.{p_end}
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
lets one {cmd:by()} graph draw 250 groups.  A global must be a whole number
from 1 to its ceiling, written in digits; anything else is refused with
{cmd:r(198)}.  An unset global means the default.  {cmd:dash clear} does not
drop these globals, because they are settings rather than registry;
{cmd:macro drop dash_max_*} does.

{pstd}
{ul:What the data limit counts.}  {cmd:dash} still exports every
observation of the variables a dashboard uses -- the data file on disk is
unchanged, and each distinct qualifier is one more exported column,
counted like a variable -- but the {cmd:$dash_max_cells} limit itself
counts only what the saved page will actually embed.  A graph drawn from
rows -- or touched by a {cmd:filter()} that does not exclude it, a
{cmd:link()}, {cmd:csv}, or {cmd:hover()} -- counts its variables and
qualifier columns times the observations, as before; the variables
{cmd:hover()} names are among its counted variables when a layer of the
graph can show them.  A graph made only of computed layers, or of
{cmd:scatteri}, {cmd:pci}, {cmd:pcarrowi} or {cmd:function}, exports its
{cmd:hover()} variables but does not count them unless {cmd:csv} is
given.  A graph made only
of computed layers ({cmd:histogram}, {cmd:kdensity}, {cmd:lfit} and the
other fits and smoothers) that nothing else reaches draws its own bounded
output instead: a histogram's bars (four values a bin, the observations
themselves only under {cmd:width()} or {cmd:discrete} with no
{cmd:bin()}), a {cmd:lowess} curve (two values an observation, so it
never escapes the cap on its own), and every other computed layer at most
120,000 values.  KPI cards and {cmd:filter()} variables always count,
whatever draws from them.  So a {cmd:histogram} on six million
observations now builds a saved page -- a few dozen bars, not six million
rows -- where a {cmd:scatter} of the same data is still refused.  A
served app is unaffected: it embeds every observation of every variable
it uses, because a live session can move a filter to any value, and says
so in its own refusal.  Reduce the data first -- {cmd:keep}, {cmd:drop},
{cmd:sample} or {cmd:collapse}, inside {cmd:preserve} and {cmd:restore} --
when a row-drawing graph, a KPI or a filter is what is over the limit.
Above 1,000,000 embedded values {cmd:dash} notes the size the file will
be, at about 24 bytes a value, which is what a saved page takes; a served
app's file carries the values as text and takes up to about twice that.
Measured, 4,000,000 values made a 95 MB page and took about 2 GB of
memory to render.  A string value adds its own length to that, and a
{cmd:strL} is exported whole, so text is held to {cmd:$dash_max_bytes} as
well: 60 observations of a 1,000,000-byte {cmd:strL} are only 60 values
but 60,000,000 bytes, and are refused at the default.  A saved page may
hold fewer observations than the limit counts: only those its graphs, cards
and filters select (see {help dash##description:Description}); the size the
dashboard reports when it is large counts those, and a served app's report
counts every observation.

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
Observations with a missing {cmd:by()} value are left out unless
{cmd:missing} is given.

{synoptset 30}{...}
{synopt:{opt by(varlist)}}facet graph by the values of {it:varlist}{p_end}
{synopt:{opt by(varlist, cols(#))}}arrange facet panels in {it:#}
    columns{p_end}
{synopt:{opt by(varlist, total)}}add a "Total" panel of every group's
    observations{p_end}
{synopt:{opt by(varlist, missing)}}include a panel, titled "Missing", of
    the observations with a missing value{p_end}
{synopt:{opt by(varlist, yrescale|xrescale|rescale)}}draw each panel on its
    own y scale, x scale or both; abbreviations {cmd:yr}, {cmd:xr} and
    {cmd:r}, and {cmd:noyrescale}, {cmd:noxrescale} and {cmd:norescale}
    ({cmd:noyr}, {cmd:noxr}, {cmd:nor}) to keep one scale; when both are
    given, the rescale wins, as in {cmd:twoway}{p_end}
{synopt:{opt by(varlist, style(rescale))}}and style(combine): only
    their separate scales are drawn, with a note{p_end}
{synoptline}

{pstd}
As in {cmd:twoway}, a {cmd:by()} graph's panels share one scale per axis --
y, x and a second axis -- spanning every panel's data, the Total panel's
too, and they keep sharing it after a filter move.  Panning or zooming one
panel moves the others, and, as in any Bokeh plot, stops that axis
following later filter moves.  With {cmd:yrescale}, {cmd:xrescale} or
{cmd:rescale} each panel is drawn and ticked ({cmd:#}{it:N}) over its own
data on that axis; there {cmd:yscale(range())} and {cmd:xscale(range())},
those of the second axis included, are not applied, as in {cmd:twoway},
and a note says so; labels and ticks still widen each panel, and reverse
and log are kept.  {cmd:twoway} draws only the outer axes of shared panels,
where {cmd:dash} draws every panel's.

{pstd}
The Total panel draws the observations of every group, as {cmd:twoway}'s
does: those with a missing {cmd:by()} value only with {cmd:missing}.
{cmd:twoway} titles the missing panel "(missing)".

{pstd}
The panels are arranged the same way wherever the graph is drawn -- in the
dashboard's grid, in a tab, or in a {cmd:layout(bs)} cell -- and in both
{cmd:dash build} and {cmd:dash serve}: in {it:#} columns with
{cmd:cols(}{it:#}{cmd:)}, and otherwise in as many columns as the square
root of the number of panels, rounded up.  A {cmd:cols()} of more columns
than there are panels puts them all in one row.

{pstd}
A panel is titled with its value's label, when the value has one, and
otherwise with the value as {cmd:twoway} writes it -- {cmd:3}, {cmd:.25} --
whatever its display format; a string variable's panels are titled with
their text, and a date variable's with their dates in its display format
({cmd:01jan2000}, {cmd:2000m1}), where {cmd:twoway} writes the number
({cmd:14610}).  Several {cmd:by()} variables produce
composite titles, "Domestic / 3", which {cmd:twoway} writes "Domestic, 3".
A graph's own {cmd:title()} leads each of its panels' titles.
One graph draws at most 100 groups by default, a panel each, and its Total
panel one more: over that, the first 100 groups in sort order are drawn and
a note names the limit and the global that raises it (see
{help dash##limits:Resource limits}).
{cmd:cols()}, {cmd:total}, {cmd:missing} and the rescale forms above are
the {cmd:by()} sub-options {cmd:dash} implements.  Any other sub-option of Stata's {cmd:by()} -- for
example {cmd:rows()}, {cmd:holes()} or {cmd:compact} -- is accepted, named
in a warning, and ignored.
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
    the value of {it:varname}, on the plot types listed below{p_end}
{synopt:{cmdab:mlabc:olor(}{it:color}{cmd:)}}color of the label text{p_end}
{synopt:{cmdab:mlabs:ize(}{it:size}{cmd:)}}a text size in Stata's units:
    a {cmd:gsize} keyword ({cmd:small}, {cmd:medium}, {cmd:large}), a
    number, a number with a unit or a {cmd:*}{it:#} multiplier{p_end}
{synopt:{cmdab:mlabp:osition(}{it:#}{cmd:)}}clock position of the label
    around the point, a whole number from 0 to 12, placed as {cmd:twoway}
    places it: 3 = right (the default), 12 = above, 6 = below, 9 = left,
    the hours between at the corners, and 0 centred on the point.  Anything
    else -- {cmd:13}, {cmd:2.5}, {cmd:03} or a name -- is reported and the
    label drawn at 12, where {cmd:twoway}, noting it, draws it{p_end}
{synopt:{cmdab:mlabg:ap(}{it:size}{cmd:)}}space between the marker's
    edge and the label, in the direction of the clock position: a
    {cmd:gsize} in Stata's units, {cmd:half_tiny} (2 point) by default, as
    in {cmd:twoway}.  It is measured from half the layer's marker size
    ({cmd:msize()} when given), on {cmd:bar}, {cmd:pcarrow} and
    {cmd:pcbarrow} too, where no marker is drawn.  A negative gap moves the
    label toward the point, and at {cmd:mlabposition(0)} the label is
    centred on its point.  {cmd:dash} also takes
    a synonym, {cmd:mlg()}, which {cmd:twoway} does not accept{p_end}
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
{synoptline}

{pstd}
{ul:Where labels are drawn.}  {cmd:scatter}, {cmd:connected}, {cmd:bar},
{cmd:dot} and {cmd:dropline} label each point.  {cmd:rcapsym},
{cmd:rconnected} and {cmd:rscatter} label both ends of each range, as
{cmd:twoway} does, and an end that is missing is left unlabelled on its
own.  {cmd:pcscatter}, {cmd:pccapsym}, {cmd:pcarrow} and {cmd:pcbarrow}
label the first point, ({it:y1var}, {it:x1var}) -- the tail of an arrow.
{cmd:twoway}'s {cmd:headlabel}, which moves those labels to the second
point, is not implemented: {cmd:dash} names it in the note and draws the
labels at the first point.  A paired-coordinate observation with a missing
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
value label or its name, which {cmd:dash} cannot do, because the data it is
handed carry every missing value alike.

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
changes an estimate is honoured or refused; the few {cmd:dash} cannot
compute -- {cmd:area()} and {cmd:boundary} on {cmd:kdensity}, a kernel
written as an option of its own (a bare {cmd:gaussian}), {cmd:atobs},
{cmd:estcmd()}, {cmd:estopts()} and {cmd:predopts()} on the fits --
are named in the note as ignored.  {cmd:pwidth()} and {cmd:var()} are
honoured on {cmd:lpolyci}; on {cmd:lpoly}, {cmd:scatter}, {cmd:lfitci},
{cmd:kdensity} and the other types, where {cmd:twoway} refuses them with
r(198), {cmd:dash} names them in the note and draws the layer.  {cmd:fpfit} and {cmd:fpfitci} take none of the smoothing
options -- see below.

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
    below).  A positive number, at most 1 on {cmd:lowess};
    {cmd:twoway}'s {cmd:kdensity} also takes {cmd:bwidth(0)}, meaning the
    default, and its {cmd:lowess} reads a fraction of 0, or of 1 or more,
    as 0.8, where {cmd:dash} reads 1 as 0.8 and refuses the rest, r(198).
    On {cmd:kdensity}, {opt width(#)} is a synonym, as in {cmd:twoway},
    and the two together are refused, r(198).  {cmd:bw()} abbreviates
    {cmd:bwidth()} on these four types, as in {cmd:twoway}; on {cmd:bar},
    {cmd:rbar}, {cmd:histogram}, {cmd:dot} and {cmd:spike} {cmd:dash}
    reads {cmd:bw()} as {cmd:barwidth()}, a synonym of its own
    ({cmd:twoway} refuses {cmd:bw()} there), and on any other plot type
    names it in the note{p_end}
{synopt:{opt pwidth(#)}}{cmd:lpolyci}: the pilot bandwidth of the
    band's variance estimate, in the units of x; by default 1.5 times the
    rule of thumb under {it:Default bandwidth}, even when {cmd:bwidth()}
    is given, as Stata's {cmd:r(pwidth)}.  A positive number; anything
    else is refused in {cmd:twoway}'s words, r(198).  {cmd:pw()} is its
    shortest spelling ({cmd:p()} is {cmd:pstyle()}, as in {cmd:twoway}).
    {cmd:pwidth(+800)} is read as 800, where {cmd:twoway} says
    {cmd:expression invalid}, r(3000){p_end}
{synopt:{opt var(#)}}{cmd:lpolyci}: a constant residual variance for the
    band, in place of the pilot fit's; the pilot window must still hold
    two observations, as in Stata, or that point has no band.  A positive
    number: zero or less is r(198), and a value that is not one number
    r(7), each in {cmd:twoway}'s words.  {cmd:v()} is its shortest
    spelling{p_end}
{synopt:{opt degree(#)}}{cmd:lpoly} and {cmd:lpolyci}: the degree of the
    local polynomial -- 0, the Nadaraya-Watson kernel estimator (the
    default); 1, local linear; 2, local quadratic; 3, local cubic.
    {cmd:twoway} takes any whole number from 0 up; {cmd:dash} refuses more
    than 3, r(198), because it fits local polynomials up to degree
    3{p_end}
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
    with {cmd:r(134)}.  On these types {cmd:dash} takes 2 to 10000;
    {cmd:twoway} takes any whole number from 1 up, with no upper bound
    ({cmd:lpoly} reads 1 as 50).  {cmd:mspline}: the number of points
    drawn between each pair of adjacent knots, default 10, 1 to 300, as in
    {cmd:twoway}.  {cmd:twoway}'s {cmd:fpfitci} and {cmd:mband} accept
    {cmd:n()} and draw the same points without it, and so does
    {cmd:dash}{p_end}
{synopt:{opt bands(#)}}{cmd:mspline} and {cmd:mband}: the number of
    equal-width bands the range of x is cut into, 1 to 200, as in
    {cmd:twoway}.  The default is {cmd:twoway}'s:
    round(min(10 log10 {it:N}, sqrt {it:N})), and at least
    min({it:N}, 2), {it:N} the plot's observations{p_end}
{synopt:{opt range(# #)}}the span of x a layer is drawn over.  On
    {cmd:lfit}, {cmd:qfit}, {cmd:lfitci} and {cmd:qfitci} the fitted line
    and its band are drawn from one number to the other -- beyond the data
    where the span is wider -- instead of over the observed range of x; on
    {cmd:kdensity} the density is estimated over it instead of from the
    minimum to the maximum of the plot's sample; on {cmd:function} it is
    the range of x, default {cmd:range(0 1)}.  Two numbers, in either
    order.  {cmd:twoway} also takes a missing end ({cmd:.}, the observed
    minimum or maximum) on the fits, and a variable, whose range is used,
    on {cmd:kdensity} and {cmd:function}; {cmd:dash} refuses both, r(198).
    {cmd:twoway} refuses {cmd:range()} on {cmd:fpfit}, {cmd:fpfitci},
    {cmd:lpoly}, {cmd:lpolyci}, {cmd:lowess}, {cmd:mspline}, {cmd:mband},
    {cmd:histogram}, {cmd:scatter} and {cmd:line}{p_end}
{synopt:{opt base(#)}}{cmd:bar}, {cmd:spike}, {cmd:dropline} and
    {cmd:area}: the value the bars, spikes, drops and area are drawn from;
    any number, default 0.  With no {cmd:base()}, when 0 lies outside the
    range of y, {cmd:twoway} draws them from the edge of the plot region
    and its axis does not reach 0; {cmd:dash} draws them from 0.
    {cmd:twoway} also takes {cmd:base()} on {cmd:dot}, where it matters
    only with {cmd:dotextend(no)}, and on {cmd:function}, as the base of
    {cmd:droplines()} -- neither of which {cmd:dash} draws -- and refuses
    it on {cmd:histogram}, {cmd:kdensity}, {cmd:rbar}, {cmd:rspike},
    {cmd:rarea}, {cmd:scatter}, {cmd:line}, {cmd:connected} and
    {cmd:lfit}{p_end}
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
    running line{p_end}
{synopt:{opt noweight}}{cmd:lowess} only: the tricube weights are
    dropped{p_end}
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
{cmd:twoway} sizes it (see {cmd:n()} above).

{pstd}
{bf:Note on {cmd:bwidth()} for {cmd:lowess}.}  Stata gives the same option
name two different meanings: for {helpb twoway lpoly} it is an absolute
bandwidth in x units, while for {helpb twoway lowess} it is the
{it:fraction} of the sample used in each local regression (default 0.8).
{cmd:dash} follows Stata in both cases, and draws {cmd:bwidth(1)} at
0.8, as Stata's {cmd:lowess} does.

{pstd}
{bf:Default bandwidth.}  With no {cmd:bwidth()}, {cmd:lpoly} and
{cmd:lpolyci} use {cmd:lpoly}'s rule of thumb as Stata computes it (see
{it:Methods and formulas} in {helpb lpoly}): a global polynomial of
degree p+3 in powers of x, where p is the degree and an even degree uses
the next odd one, with Stata's handling of nearly collinear powers; the
residual variance as the weighted mean squared residual of that fit; the
squared (p+1)th derivative of the fit integrated over the central 90% of
the range of x; and Stata's constant for the kernel.  The bandwidth is
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
a band's edge belongs to the band above it.  {cmd:mband} draws the same
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
{cmd:dash} does not honour: it names {cmd:estopts()} in the note.
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
refuses it.  On any {cmd:histogram} a {cmd:start()} above the smallest
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
{cmd:level(}{it:#}{cmd:)} must be a number strictly between 0 and 100
and is refused otherwise, with r(198); {cmd:twoway} takes any number
there.  On {cmd:lpolyci} it is {cmd:twoway}'s rule: 10 to 99.99, with at
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
{it:#} from 1 to 15, draws the band and the line in that plot style, and
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
    {cmd:twoway} draws it, the colour blended towards white{p_end}
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
plot types {cmd:acolor()}, {cmd:alcolor()}, {cmd:alwidth()},
{cmd:alpattern()} and {cmd:pstyle()} are named in the note (see
{help dash##unsupported:Unsupported Stata twoway options}).
{cmd:astyle()} and {cmd:alstyle()} are not honoured, and are named.

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
({cmd:weights not allowed}).  The weight must be one existing variable,
abbreviated as {cmd:twoway} abbreviates a variable.  {cmd:twoway} also
accepts an expression there; {cmd:dash} cannot evaluate one before the
data leave Stata, so it is refused with r(198) and the remedy:

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash lfit mpg weight [aw=price+1]}{p_end}
{phang3}{cmd:dash: [aweight=price+1] must name one variable; dash cannot evaluate a weight expression. Generate it first: generate double w = price+1}{p_end}

{pstd}
On {cmd:scatter} and the other glyph layers, and on {cmd:function}, a
weight is accepted so a pasted command still runs, but it is not drawn
({cmd:twoway scatter} sizes its markers by an {cmd:aweight}; {cmd:dash}
does not), and it is named in the note by type, never by variable, as
{cmd:[aweight]}.  On a statistical layer that takes it the weight is
exported with the data; on a glyph layer the weight variable is not
exported.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash (scatter mpg weight) (lfitci mpg weight [aw=price]), saving(w.html)}{p_end}


{marker region_options}
{title:Region Styling Options}

{pstd}
{cmd:dash} reads the {helpb twoway} region options that color the inner
plot area and the outer graph region, in the saved dashboard and the served
app alike.

{synoptset 35}{...}
{synopt:{cmd:plotregion(color(}{it:color}{cmd:))}}background color of the
    inner plot canvas; Bokeh {cmd:background_fill_color}.
    {cmd:plotregion(fcolor())} is read the same way{p_end}
{synopt:{cmd:plotregion(lcolor(}{it:color}{cmd:))}}border line color
    of the inner plot area; Bokeh {cmd:outline_line_color}{p_end}
{synopt:{cmd:plotregion(lwidth(}{it:#}{cmd:))}}border line width
    of the inner plot area, a number or a width name such as {cmd:thick};
    Bokeh {cmd:outline_line_width}{p_end}
{synopt:{cmd:graphregion(color(}{it:color}{cmd:))}}background color of the
    outer margin area; Bokeh {cmd:border_fill_color}{p_end}
{synopt:{cmd:graphregion(fcolor(}{it:color}{cmd:))}}fill color alias for
    {cmd:graphregion(color())}{p_end}
{synopt:{cmdab:bgc:olor(}{it:color}{cmd:)}}read as
    {cmd:graphregion(color())}{p_end}
{synopt:{opt plotbgcolor(color)}}{cmd:dash}'s own shorthand for
    {cmd:plotregion(color())}; {cmd:twoway} refuses {cmd:plotbgcolor()}.
    Synonym: {cmd:pbgc()}{p_end}
{synoptline}

{pstd}
Each of these takes a Stata named color ({cmd:navy}, {cmd:maroon},
{cmd:forest_green}, etc.), an RGB triplet in quotes ({cmd:"255 0 0"}), or a
hex string ({cmd:#1a476f}).  An unknown color is named in a note and the
scheme's color is kept.  {cmd:twoway}'s own {cmd:bgcolor()} paints the
canvas under the graph region, which shows only where the graph region has
no color of its own; {cmd:dash} colors the graph region itself.

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
{synopt:{cmdab:zti:tle(}{it:string}{cmd:)}}title of the colour key; see {cmd:colorvar()}{p_end}
{synopt:{cmdab:zlab:el(}{it:#}[{it:#} ...]{cmd:)}}colour-bar tick positions; see {cmd:colorvar()}{p_end}
{synopt:{cmdab:zsc:ale(}{it:range() log reverse}{cmd:)}}colour-bar range, scale and direction; see {cmd:colorvar()}{p_end}
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
{synopt:{cmdab:leg:end(position(}{it:#}{cmd:))}}place legend by Stata clock
    position, outside the plot: 12 is above, 3 right, 6 below, 9 left{p_end}
{synopt:{cmdab:leg:end(ring(0))}}keep the legend inside the plot region
    rather than beside it{p_end}
{synopt:{cmdab:leg:end(cols(}{it:#}{cmd:))}}arrange legend entries in {it:#} columns{p_end}
{synopt:{cmdab:leg:end(rows(}{it:#}{cmd:))}}arrange legend entries in {it:#} rows{p_end}
{synopt:{cmdab:leg:end(order(}{c -(}{it:#}|{cmd:-}{c )-} [{it:"text"} ...] ...{cmd:))}}select
    and order the keys by plot number, retitle one with text after its
    number, or insert a text-only line after {cmd:-}; a key left out is
    dropped and a number given twice draws the key twice{p_end}
{synopt:{cmdab:leg:end(size(}{it:size}{cmd:))}}font size of the legend text{p_end}
{synopt:{cmdab:leg:end(label(}{it:#} {it:"text"}{cmd:))}}override the label for plot {it:#}{p_end}
{synopt:{cmdab:leg:end(lastlabel(}{it:#} {it:"text"}{cmd:))}}the last label applied,
    over {cmd:order()} and {cmd:label()}, to the {it:#}th row as drawn{p_end}
{synopt:{cmdab:xsiz:e(}{it:#}{cmd:)}}graph width in inches; see
    {help dash##geometry:Figure proportions}{p_end}
{synopt:{cmdab:ysiz:e(}{it:#}{cmd:)}}graph height in inches{p_end}
{synopt:{cmdab:xtic:k(}{it:#}[{it:#} ...]{cmd:)}}x-axis tick positions
    without labels{p_end}
{synopt:{cmdab:ytic:k(}{it:#}[{it:#} ...]{cmd:)}}y-axis tick positions
    without labels{p_end}
{synopt:{cmdab:hov:er(}{it:varlist}{cmd:)}}{cmd:dash}'s own: add the
    variables' values to the tooltip; see {it:Tooltips} below.
    {cmd:twoway} refuses it{p_end}
{synoptline}

{pstd}
A legend's sub-options are read as sub-options: a word inside a quoted
label, such as {cmd:label(1 "Turned off")}, is text, never {cmd:off}.
A label's text is read as {cmd:twoway} reads a title's: each string is a
line, so {cmd:label(1 "top" "bottom")} is two; a string in compound
quotes keeps the quotes it holds, nested compound quotes included; and
text with no double quote is one line.
Keys are numbered as {cmd:twoway} numbers its plots: a confidence-interval
fit such as {cmd:lfitci} is two, its band {it:n} and its line {it:n}+1.
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
form keep the axis's default ticks, with a note.

{pstd}
Any of those may be followed by a comma and the sub-options
{cmd:format(}{it:fmt}{cmd:)}, {cmd:labsize(}{it:size}{cmd:)},
{cmd:angle(}{it:#}{cmd:)}, {cmd:grid} or {cmd:nogrid}, and
{cmd:valuelabel} (the axis variable's value labels at the ticks), and
{cmd:norescale}.  As in {cmd:twoway}, label and tick positions widen the
axis to include them, unless {cmd:norescale} is given, which draws them
without widening it; {cmd:twoway} drops {cmd:norescale} from a lone
{it:a}{cmd:(}{it:b}{cmd:)}{it:c} rule and widens that axis anyway, and so
does {cmd:dash}.  {cmd:xscale(range(}{it:numlist}{cmd:))} /
{cmd:yscale(range(}{it:numlist}{cmd:))} widen the axis to include every
value listed, in any order; they never narrow it or hide data.  One value
is one value to include ({cmd:yscale(range(0))} reaches 0 and keeps the
data's top), a missing value is ignored, {cmd:r()} is the abbreviation
and {cmd:rev} that of {cmd:reverse}; a value that is not a number is named
and ignored.  The axis then runs over the hull of its data, positions and
{cmd:range()} values with a margin of 5% of that span at each end (in log
units on a log axis; {cmd:twoway}'s margin is a fixed part of the graph
instead), and holds across filter moves.

{pstd}
{cmd:#}{it:N} puts the ticks where {cmd:twoway} does: at 1, 2 or 5 times a
power of ten, chosen over the smallest and largest values the axis's layers
draw, and the axis reaches its outermost tick; so {cmd:ylabel(#5)} on
{cmd:auto}'s {cmd:mpg} labels 10 20 30 40.  {cmd:#1} labels the smallest and
largest values.  {cmd:twoway}'s rule is compiled into Stata, so {cmd:dash}
reproduces it from Stata's own answers: it agrees with 261 of 264 axes
{cmd:twoway} drew and with 98% of random ranges, and where it differs it
draws a tick more or fewer at an end.  {cmd:xtick(#}{it:N}{cmd:)} and
{cmd:ylabel2(#}{it:N}{cmd:)} use the same rule.  On a log axis the rule is
the same, over the data's own values, and a tick at or below zero, which a
log axis cannot draw, is left out: {cmd:yscale(log) ylabel(#5)} on
{cmd:price} labels 5,000 10,000 15,000.  A {cmd:%tc} axis takes the same
rule over Stata's milliseconds.  A {cmd:%td}, {cmd:%tw}, {cmd:%tm},
{cmd:%tq}, {cmd:%th} or {cmd:%ty} axis is ticked on calendar boundaries
(days, weeks, the first days of months, quarters and years) by
{cmd:twoway}'s time-series rule, also compiled; {cmd:dash} follows a model
of it fitted to 12,000 of Stata's answers, which agrees exactly with 98% of
{cmd:%ty} ranges and with 52% to 66% of the others, and where it differs
it picks another calendar step or end tick.  A {cmd:by()} graph's panels
are ticked on one scale, over all the panels' data, as {cmd:twoway} ticks
them; with {cmd:by(, yrescale)} each panel is ticked over its own data,
as {cmd:twoway} ticks it.

{pstd}
A date axis's ticks are written in the axis variable's display format, as
{cmd:twoway} writes them: a {cmd:%tm} axis reads {cmd:2001m1 2001m4}, a
{cmd:%td} axis {cmd:02jan2001}, a custom picture as written.  An explicit
{cmd:format()} of any numeric display format ({cmd:%f}, {cmd:%g},
{cmd:%e}) writes the ticks as Stata's {cmd:display} does.

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
{ul:Ticks without labels.}  {cmd:xtick()} and {cmd:ytick()} add ticks
without labels beside whatever labels the axis has, its default ones or
those {cmd:xlabel()} and {cmd:ylabel()} ask for.  They take a numlist or
{it:a}{cmd:(}{it:b}{cmd:)}{it:c}, {cmd:#}{it:N} or {cmd:minmax}, and the
sub-option {cmd:grid}, which draws gridlines at the ticks; another
sub-option is named in a warning.  Bokeh labels one set of ticks per axis,
so these are drawn as its minor ticks, at the major ticks' length; Bokeh's
own minor ticks, which Stata does not draw, are not drawn on that axis.
With {cmd:axis(2)} the ticks are on the second axis's scale, and they
widen that axis, as a label does, unless {cmd:norescale} is given; a line,
{cmd:yline(}{it:#}{cmd:, axis(2))}, never widens an axis.

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
takes 1 or 2 only: {cmd:dash} draws two axes where {cmd:twoway} allows
nine, and any other value is refused.

{pstd}
As in {cmd:twoway}, the sub-option {cmd:axis(2)} puts {cmd:ytitle()},
{cmd:ylabel()}, {cmd:ytick()}, {cmd:yline()} and {cmd:yscale()} -- and the
x forms -- on the second axis, and {cmd:axis(1)}, or no {cmd:axis()}, on the
first: {cmd:ylabel(5000 10000, axis(2))} labels the right-hand axis,
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
{cmd:ymlabel()} and {cmd:ymtick()} are checked the same way but are drawn
on neither axis (named in a warning).  {cmd:add} on a label routed to the
second axis ({cmd:ylabel(5000, axis(2) add)}) is named, not applied.  The
second axes also take the options below, which are {cmd:dash}'s own
spellings of the {cmd:axis(2)} forms, as are their synonyms:
{cmd:twoway} refuses all sixteen, r(198).  Given on a graph with no layer
on that second axis, they are named in a warning when the dashboard is
built, saved or served.

{pstd}
When every layer of a graph is on {opt yaxis(2)}, {cmd:dash} draws one y
axis, on the left, as {cmd:twoway} does; the {cmd:axis(2)} forms --
{cmd:ytitle2()}, {cmd:ylabel2()}, {cmd:yscale2()}, {cmd:ytick2()} and
{cmd:yline2()} -- style it, and the first axis's options are refused,
r(198), with {cmd:twoway}'s message ({cmd:ylabels(5000 10000) not allowed,}
{cmd:yaxis1 does not exist}).  When every layer is on {opt xaxis(2)}, the
one x axis is drawn at the bottom, styled the same way by the x forms.

{synoptset 38}{...}
{synopt:{opt ytitle2(tinfo)}}title for the right-hand y axis, in the
    textbox grammar every text option takes: one or more quoted strings,
    each its own line, and {cmd:size()}/{cmd:color()} honoured.
    Synonym: {cmd:yti2()}{p_end}
{synopt:{opt ylabel2(rule)}}labels for the right-hand y axis, in the
    grammar {cmd:ylabel()} takes.  Synonym: {cmd:yla2()}{p_end}
{synopt:{opt yscale2(log)}}log scale on the right-hand y axis.
    Synonym: {cmd:ysc2()}{p_end}
{synopt:{opt xtitle2(tinfo)}}title for the top x axis, in the same
    textbox grammar.  Synonym: {cmd:xti2()}{p_end}
{synopt:{opt xlabel2(rule)}}labels for the top x axis, in the grammar
    {cmd:xlabel()} takes.  Synonym: {cmd:xla2()}{p_end}
{synopt:{opt xscale2(log)}}log scale on the top x axis.
    Synonym: {cmd:xsc2()}{p_end}
{synopt:{opt ytick2(rule)}}ticks without labels on the right-hand y axis,
    in the grammar {cmd:ytick()} takes; twoway writes it with the
    sub-option axis(2).  No abbreviation.{p_end}
{synopt:{opt xtick2(rule)}}ticks without labels on the top x axis.  No
    abbreviation.{p_end}
{synopt:{opt yline2(linelist)}}lines at the right-hand y axis's values, as
    {cmd:yline()} draws them; twoway writes it with the sub-option
    axis(2).  No abbreviation.{p_end}
{synopt:{opt xline2(linelist)}}lines at the top x axis's values.  No
    abbreviation.{p_end}
{synoptline}

{pstd}
{cmd:ytitle2()} and {cmd:xtitle2()} are read the same way every other
text option is: each quoted string is its own line, {cmd:size()} and
{cmd:color()} are applied, and any other sub-option is named once.  An
empty string ({cmd:ytitle2("")}) removes the title; without one, the
second axis is titled as {cmd:twoway} titles it -- by the label (or
name) of its first layer's variable, {cmd:Density} or {cmd:kdensity}
{it:varname} for those layers -- in the scheme's axis style, and
sub-options alone style that title; under {cmd:by()} it has no default
title, as in {cmd:twoway}.

{pstd}
{cmd:ylabel2()} and {cmd:xlabel2()} read their rule and sub-options with
the parser {cmd:ylabel()} uses: a numlist, {cmd:#}{it:N},
{it:a}{cmd:(}{it:b}{cmd:)}{it:c}, {cmd:minmax}, {cmd:none}, value-label
pairs, {cmd:format()}, {cmd:labsize()}, {cmd:angle()} and {cmd:grid}, which
draws gridlines at the second axis's ticks; any other sub-option is named
in a warning.  {cmd:yscale2()} and {cmd:xscale2()} take {cmd:log},
{cmd:reverse} ({cmd:rev}) and {cmd:range(}{it:numlist}{cmd:)} ({cmd:r()}),
which widens the second axis only, as {cmd:yscale(range())} does, and
name anything else; {cmd:ylabel2()} and {cmd:xlabel2()} positions widen
the second axis unless {cmd:norescale} is given.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse sp500, clear}{p_end}
{phang2}{cmd:. dash (line close date) (line volume date, yaxis(2)), ytitle2(Volume (thousands))}{p_end}

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
{cmd:rline}, {cmd:tsrline}, {cmd:rconnected}, {cmd:rscatter}) and every
paired-coordinate type drawn from variables ({cmd:pcspike},
{cmd:pcarrow}, {cmd:pcbarrow}, {cmd:pcscatter}, {cmd:pccapsym}) -- in the
saved dashboard and the served app alike.  Each point shows the values of
its own observation; both points of an {cmd:rscatter} or a
{cmd:pcscatter} show the same one.  A computed layer's points are not
observations -- {cmd:lfit}, {cmd:qfit}, {cmd:lfitci}, {cmd:qfitci},
{cmd:fpfit}, {cmd:fpfitci}, {cmd:lowess}, {cmd:lpoly}, {cmd:lpolyci},
{cmd:mband}, {cmd:mspline}, {cmd:kdensity}, {cmd:histogram} and
{cmd:function} -- and an immediate layer's ({cmd:scatteri}, {cmd:pci},
{cmd:pcarrowi}) are typed in the command, so {cmd:hover()} cannot reach
them: their tooltips, where they have one, show only what the layer draws,
x and y or a histogram's bin and count, and {cmd:dash} names each such
layer in a note, once.  A variable's value is written in its display
format, as Stata's {cmd:display} writes it -- {cmd:4,099} under
{cmd:%8.0gc}, {cmd:12345.67} under {cmd:%10.0g}, a date in its picture,
a {cmd:%tc} or {cmd:%tC} date with its time -- in both render modes.
Every variable {cmd:hover()} names is exported with the data, whether or
not a layer plots it, so its value is in the tooltip of the saved
dashboard and the served app, before and after a filter move; its values
are part of the saved page's source, like the variables the layers draw.
It counts toward {cmd:$dash_max_cells}, and a string one also toward
{cmd:$dash_max_bytes}, on the saved page when a layer of its graph can
show it or {cmd:csv} is given, and always in a served app (see
{help dash##limits:Resource limits}).  {cmd:dash build} and
{cmd:dash serve} refuse a {cmd:hover()} variable no longer in memory with
r(111), as they refuse a dropped plotted variable.


{marker colorvar}
{title:Mapping a Variable to Colour}

{pstd}
{cmd:colorvar(}{it:varname}{cmd:)} colours each observation of a layer by a
third variable instead of by the scheme's series colour.  {cmd:dash} draws
it on {cmd:scatter}, {cmd:dot}, {cmd:connected} and {cmd:rconnected} -- on
their markers; a connecting line keeps the series colour.  {cmd:twoway}
accepts {cmd:colorvar()} on every plot type, and colours {cmd:line} and
{cmd:bar}, though not {cmd:area} or {cmd:lfit}.  On any type but
{cmd:scatter}, {cmd:dot}, {cmd:connected} and {cmd:rconnected}, {cmd:dash}
names {cmd:colorvar()} and each of its companions in its note and draws the
layer in the series colour.  A companion written without {cmd:colorvar()}
is named too.

{synoptset 38}{...}
{synopt:{cmdab:colorv:ar(}{it:varname}{cmd:)}}colour each observation by
    {it:varname}.  Synonyms, {cmd:dash}'s own: {cmd:colv()}, {cmd:cv()}{p_end}
{synopt:{cmdab:colordis:crete}}treat {it:varname} as categorical: one
    colour per value{p_end}
{synopt:{cmdab:colorcut:s(}{it:numlist}{cmd:)}}explicit break points for the
    colour bins{p_end}
{synopt:{cmdab:colpal:ette(}{it:name}{cmd:)}}the palette to map through:
    {cmd:viridis} (the default for an unbinned {it:varname}), {cmd:magma},
    {cmd:inferno}, {cmd:plasma}, {cmd:cividis}, {cmd:turbo}, {cmd:greys},
    {cmd:blues} or {cmd:reds}{p_end}
{synopt:{cmdab:colorn:levels(}{it:#}{cmd:)}}number of equal-width colour
    bins for a numeric {it:varname}; an integer from 2 to 256{p_end}
{synopt:{cmdab:colorm:issing(}{it:color}{cmd:)}}colour drawn for observations
    where {it:varname} is missing{p_end}
{synopt:{cmdab:colorlev:els(}{it:#}{cmd:)}}# levels: # - 1 equally spaced cuts
    between the minimum and maximum (Stata's spelling; {cmd:colornlevels()} is
    the same); as in {cmd:twoway}, 0 and 1 draw as if it were absent, and a
    negative number or one over 100 draws 5 levels{p_end}
{synopt:{cmdab:colorvarminm:ax}}add the minimum and maximum of {it:varname} to
    the cuts, and to the colour bar's ticks{p_end}
{synoptline}

{pstd}
{cmd:colorvar()}, {cmd:colordiscrete}, {cmd:colorcuts()},
{cmd:colorlevels()} and {cmd:colorvarminmax} are Stata 18's own and drawn as
Stata draws them: under {cmd:colordiscrete} the cuts are the levels and every
other value is drawn in {cmd:colormissing()}'s colour with the missing
values; a cut below the minimum is ignored, and the minimum is used if all
are; {cmd:colorcuts()} and {cmd:colorlevels()} may not be combined.
{cmd:colpalette()}, {cmd:colornlevels()} and {cmd:colormissing()} are
{cmd:dash}'s, and {cmd:twoway} refuses them.  {cmd:twoway}'s other
{cmd:colorvar} options, {cmd:colorrule()}, {cmd:colorstart()},
{cmd:colorend()} and {cmd:colorformissing()}, are named in the note.  How the colours are drawn
is {cmd:dash}'s: an unbinned numeric {it:varname} is mapped continuously
through the palette and a colour bar is drawn beside the figure, where
{cmd:twoway} bins it at its z axis's ticks.  {cmd:colordiscrete},
{cmd:colorcuts()} and {cmd:colornlevels()} bin it, and a discrete key
entry is drawn per bin, in the scheme's series colours unless
{cmd:colpalette()} names a palette.  {cmd:twoway} wants a numeric
{it:varname} (a string one is r(7)); {cmd:dash} also takes a string
variable, one colour and one key entry per value, an empty string drawn in
{cmd:colormissing()}'s colour.

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
each panel colours its own observations, as {cmd:twoway} does; {cmd:dash}
draws each panel's key, where {cmd:twoway} draws none unless
{cmd:by(, clegend(on))} asks for the first panel's, and its note names
{cmd:clegend()}.  A filter move keeps the colours and the key chosen when
the dashboard was built, in both the saved page and the served app.
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
On a discrete key {cmd:zlabel()} and {cmd:zscale()} are named in the note.
{cmd:ztitle()} given only sub-options styles the key's default title, the
colour variable's label; {cmd:suffix} and {cmd:prefix} add lines to it.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, colorvar(price) colpalette(magma) colornlevels(8)}{p_end}

{pstd}
{ul:When a legend appears.}  As in {helpb twoway}, a legend is drawn only
when the graph has two or more keys: a lone {cmd:scatter} gets none, a
{cmd:scatter} with an {cmd:lfit} over it gets one.  {cmd:legend(on)} forces
one onto a single-key graph and {cmd:legend(off)} removes it from any graph.
A {cmd:colorvar()} key is not the legend: it stays.


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
These plot-level options are honoured on the plot types named, in the
saved dashboard and the served app alike, and {cmd:dash}'s note does not
name them there.

{synoptset 28}{...}
{synopt:{cmdab:jit:ter(}{it:#}{cmd:)}}move each marker by uniform noise
    spanning {it:#}% of the data's range on each axis; {it:#} must be a
    number from 0 to 100.  Drawn on the markers of {cmd:scatter},
    {cmd:connected}, {cmd:rconnected}, {cmd:dot}, {cmd:dropline} and
    {cmd:scatteri}, never on a connecting line, as in {cmd:twoway}.
    {cmd:dash} accepts {it:jit} for it, where {cmd:twoway} wants the full
    name{p_end}
{synopt:{opt jitterseed(#)}}random-number seed for {cmd:jitter()}, spelled as
    in Stata; {it:#} must be a non-negative integer.  With no seed the noise
    differs on every render{p_end}
{synopt:{cmdab:jse:ed(}{it:#}{cmd:)}}a {cmd:dash} synonym for
    {cmd:jitterseed()}, with the same bound; if both are given,
    {cmd:jseed()} wins{p_end}
{synopt:{cmdab:msa:ngle(}{it:#}{cmd:)}}rotate every marker in the layer
    {it:#} degrees counter-clockwise, as {cmd:twoway} does; {it:#} must lie
    between -360 and 360, as in {cmd:twoway}.  Drawn on every plot type
    that draws markers: {cmd:scatter}, {cmd:connected}, {cmd:rconnected},
    {cmd:dot}, {cmd:dropline}, {cmd:scatteri}, {cmd:rscatter},
    {cmd:rcapsym}, {cmd:pcscatter} and {cmd:pccapsym}{p_end}
{synopt:{opt marker(symbol)}}{cmd:dash}'s own synonym for
    {cmd:msymbol()}, which wins if both are given; {cmd:twoway} refuses
    {cmd:marker()}{p_end}
{synopt:{cmdab:col:or(}{it:color}{cmd:)}}the layer's colour -- its markers,
    lines and fills alike, as in {cmd:twoway}; {cmd:mcolor()},
    {cmd:lcolor()} and {cmd:fcolor()} win where given{p_end}
{synopt:{cmdab:mal:pha(}{it:#}{cmd:)}}opacity of the markers, 0-100{p_end}
{synopt:{cmdab:lal:pha(}{it:#}{cmd:)}}opacity of the lines, 0-100{p_end}
{synopt:{cmdab:fa:lpha(}{it:#}{cmd:)}}opacity of the fill, 0-100{p_end}
{synoptline}

{pstd}
{cmd:twoway} also jitters the markers of {cmd:rscatter}, {cmd:rcapsym},
{cmd:pcscatter} and {cmd:pccapsym}; {cmd:dash} does not, and names
{cmd:jitter()} and its seed in the note there.  {cmd:malpha()},
{cmd:lalpha()} and {cmd:falpha()} are {cmd:dash}'s own and {cmd:twoway}
refuses them; its way is Stata's {cmd:color%alpha} notation, which works
too, so {cmd:mcolor(red%50)} and {cmd:mcolor(red) malpha(50)} are the same
thing.

{pstd}
The line options {cmd:lcolor()}, {cmd:lwidth()} and {cmd:lalpha()} style a
layer's lines -- a connecting line, a drop, a spike -- and never its
markers, as in {cmd:twoway}: a marker's outline is {cmd:mlcolor()} and
{cmd:mlwidth()}, and {cmd:color()} colours markers, lines and fills
alike.  An unknown {cmd:lcolor()} or {cmd:lwidth()} name is still reported
on a plot with no line, as {cmd:twoway} notes it there.

{pstd}
{it:Example:}

{phang2}{cmd:. sysuse auto, clear}{p_end}
{phang2}{cmd:. dash scatter mpg weight, jitter(5) jitterseed(12345) malpha(60)}{p_end}


{marker scheme}
{title:Stata scheme support}

{pstd}
{cmd:scheme()} applies a named Stata graph scheme to the whole dashboard.
With no {cmd:scheme()} and no {cmd:theme()}, {cmd:dash} follows the session's
own {cmd:c(scheme)}, so a dashboard has the look of every other graph you
draw without your asking.

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
    {cmd:lcolor()}, {cmd:lpattern()} and {cmd:lwidth()} still win.
    A line given the sub-option axis(2) is drawn at that value of the
    second axis; no line widens an axis.{p_end}

{phang2}{ul:Series.}  The colour, symbol and line-pattern cycles
    ({cmd:p1} to {cmd:p15}), the line width ({cmd:linewidth p}, and
    {cmd:linewidth p}{it:#} per plot), a marker's outline width (the
    same, or {cmd:linewidth p}{it:#}{cmd:mark} and {cmd:linewidth pmark}
    where a scheme declares them; {cmd:mlwidth()} still wins), a bar's
    and an area's outline width ({cmd:linewidth pbar} and
    {cmd:linewidth parea}), the
    marker colour where a scheme
    declares a {cmd:color p}{it:#}{cmd:mark} apart from {cmd:p}{it:#}, the
    marker size ({cmd:symbolsize p}, and {cmd:symbolsize p}{it:#} per
    plot), the fill intensities, and a colour
    opacity the scheme declares ({cmd:sttrans}'s {cmd:%20}), which is
    carried into the scatter, connected, line, bar, area and histogram
    layers in both modes and wins over the alpha {cmd:dash} otherwise
    derives from the intensities; the range, spike, fit, band, density,
    function and immediate layers take the colour but not yet its opacity;
    your own {cmd:mcolor(}{it:x}{cmd:%}{it:NN}{cmd:)} or {cmd:malpha()}
    still wins over both.  Plots are numbered as {cmd:twoway} numbers
    them: a {cmd:lfitci}, {cmd:qfitci}, {cmd:lpolyci} or {cmd:fpfitci}
    draws two plots, its band and its line, so
    {cmd:lfitci} || {cmd:lfitci} || {cmd:lfit} draws its lines in
    {cmd:p1}, {cmd:p3} and {cmd:p5}, as {cmd:twoway} does.{p_end}

{phang2}{ul:Grids.}  A major grid is drawn on an axis only where the
    scheme says so ({cmd:yesno draw_major_hgrid} for the x axis,
    {cmd:draw_major_vgrid} for the y axis), in {cmd:color major_grid} at
    {cmd:linewidth major_grid}; a minor grid only where
    {cmd:draw_minor_hgrid} or {cmd:draw_minor_vgrid} says so, which no
    shipped scheme does.  So {cmd:s1color}, {cmd:s1mono}, {cmd:s1rcolor}
    and {cmd:stmono1} draw no grid at all, as in Stata.  A grid that
    {cmd:xlabel(, grid)} or {cmd:ylabel(, grid)} turns on is drawn in the
    scheme's grid colour.  Tick geometry is not the scheme's (see below):
    an axis whose labels Bokeh places, as it does by default, also carries
    Bokeh's minor ticks, which Stata draws only when {cmd:xmtick()},
    {cmd:xmlabel()} or their {it:y} twins ask for them.{p_end}

{phang2}{ul:Text.}  Each piece of text takes the size and colour of the
    Stata textbox style that draws it: {cmd:title()} is {cmd:heading},
    {cmd:subtitle()} is {cmd:subheading}, {cmd:caption()} is {cmd:body},
    {cmd:note()} is the scheme's {cmd:textboxstyle note} -- {cmd:small_body}
    in most schemes, {cmd:key_label} in {cmd:s1manual}, and in
    {cmd:economist} {cmd:reverse_big}, white {cmd:medlarge} text in a box
    filled with {cmd:color reverse_big} (Stata's note textbox does not use
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
Copy the file into the working directory instead.  The file is read the
way Stata reads it: each line is {cmd:styletype element style}, with the
style the third word, quoted when it holds blanks, as in
{cmd:color background "255 0 0"} or {cmd:color p1 "26 71 111 %20"}.  A
line that cannot be read that way is named once, with its line number,
and skipped.  A name carrying a
directory separator or {cmd:..} is refused.

{pstd}
{ul:A name that resolves to nothing is refused.}  A {cmd:scheme()} that
is neither a shipped scheme, one of the {cmd:theme()} aliases nor a
{cmd:.scheme} file in the working directory is refused before any Python
runs, on every entry point, with r(198):

{phang3}{cmd:. sysuse auto, clear}{p_end}
{phang3}{cmd:. dash scatter mpg weight, name(s1)}{p_end}
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
When {cmd:dash} cannot translate it -- a third-party scheme -- it says
so once,
{cmd:dash: 'X' is not a known theme or scheme; it was inherited from the session (c(scheme)) because no scheme() or theme() was given ...; using s2color},
and draws {cmd:s2color}; never an error, so a session set to a scheme
{cmd:dash} does not know still builds.

{pstd}
{ul:What a scheme file of yours may include.}  StataCorp's schemes are
written as edits on top of an {cmd:#include}d parent, and {cmd:dash}
resolves that chain once, when it extracts its twenty-six translations, so
each shipped file already carries every directive it needs with every
colour written as hex.  A file of yours is read the same way: an
{cmd:#include} is resolved as {cmd:scheme()} itself is -- a {cmd:.scheme}
file of that name in the working directory first, then one of the
twenty-six translations {cmd:dash} ships -- never Stata's own
{cmd:scheme-}{it:name}{cmd:.scheme}.  As in Stata, an {cmd:#include}
takes effect where it stands: the lines after it override the included
scheme, and the included scheme overrides the lines before it.  An
{cmd:#include} that resolves to neither (a third-party scheme, or a path
outside the working directory) is read as {cmd:#include s2color}, as
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
Colours may be Stata colour names or {cmd:#rrggbb}.

{pstd}
{ul:What the shipped files are.}  Each is a translation in {cmd:dash}'s
own format, not a copy of StataCorp's file and not a drop-in Stata
scheme: 80 to 140 directives (more for the monochrome schemes, whose
chains declare connecting-line and line-plot keys and a symbol cycle) where Stata's
{cmd:scheme-s2color.scheme}
has 2060, the {cmd:#include} chain flattened into the file, every colour
resolved to {cmd:#rrggbb} ({cmd:sttrans}'s with the {cmd:%20} opacity
Stata declares kept as {cmd:#rrggbb%20}, and {cmd:economist}'s plot-region
border written as Stata's {cmd:none}), and a {cmd:* provenance:}
comment for every
directive saying whether it was transcribed from Stata's file, and from
which directive, or inferred by {cmd:dash} -- the area intensity, which
Stata resolves through a fallback and {cmd:dash} writes out resolved.  The
{cmd:p}{it:#}{cmd:line}, {cmd:p}{it:#}{cmd:bar},
{cmd:p}{it:#}{cmd:mark} and {cmd:p}{it:#}{cmd:lineplot} colours, the
line patterns, the marker symbols and the marker sizes are not written
out: each file carries only the keys
Stata's own chain declares, and {cmd:dash} follows the
{cmd:p}{it:#}{it:stub} fallback itself, as Stata does.  Most of the
directives {cmd:dash} does not carry govern what it does not draw: the styling of {cmd:graph bar}, {cmd:box}, {cmd:pie},
{cmd:dot} and {cmd:matrix} charts, margins and tick geometry.  Some govern
what it draws in its own way, so those can look different from Stata's.
A confidence band's keys are carried -- {cmd:color ci_area},
{cmd:ci_arealine} and {cmd:ci_line}, {cmd:intensity ci_area},
{cmd:linewidth ci_area} and {cmd:ci}, {cmd:linepattern ci_area} and
{cmd:ci}, and {cmd:ci2}'s colours and width -- and drawn as Stata draws
them (see {help dash##ciband:The band's look}).  {cmd:graph} never reads
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
its own twenty-six names and for nothing else, so {cmd:scheme()} works the
same from an installed copy as from a source checkout, and any other
package's file in the same directory stays unread.  You still name them
as before: {cmd:scheme(s2color)} or {cmd:scheme(s2color.scheme)}.  A
{cmd:.scheme} file you put in the working directory still wins over the
shipped one of the same name.

{pstd}
{ul:Why they are named {cmd:dash-}{it:name}{cmd:.scheme}.}  The
{cmd:dash-} prefix means the files cannot collide with Stata's own
{cmd:scheme-}{it:name}{cmd:.scheme} files or with another package's
{it:name}{cmd:.scheme}, so {cmd:set scheme} {it:name} still finds Stata's
own copy and {cmd:dash}'s translations never change how {cmd:graph} draws
by default.  They are {cmd:dash}'s alone: {cmd:set scheme} looks only
for {cmd:scheme-}{it:name}{cmd:.scheme}, so it never reads them, and in
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
command copy-pasted from a do-file always runs -- and every one that is
supplied is named in that command's note, so nothing is dropped in silence:

{p 12 12 2}{cmd:. sysuse auto, clear}{p_end}
{p 12 12 2}{cmd:. dash scatter mpg weight, pstyle(p3) t1title("hi")}{p_end}
{p 12 12 2}{cmd:(note: dash: ignoring unsupported option(s): pstyle() t1title())}{p_end}

{pstd}
The note is built from the declarations in {cmd:dash.ado}, and this list is
checked against them: {cmd:test/test_help_conformance.py} fails if the two
disagree in either direction.

{phang2}{ul:Alternative titles.}
    {opt t1title(string)}, {opt t2title(string)}, {opt b1title(string)},
    {opt b2title(string)}, {opt l1title(string)}, {opt l2title(string)},
    {opt r1title(string)}, {opt r2title(string)} -- {cmd:twoway}'s titles
    above, below and beside the plot region; {cmd:dash} draws
    {cmd:title()}, {cmd:subtitle()}, {cmd:note()}, {cmd:caption()} and the
    axis titles only.  {opt title2(string)} and
    {opt subtitle2(string)} are not {cmd:twoway} options at all:
    {cmd:twoway} refuses them, r(198), and {cmd:dash} names them.

{phang2}{ul:Minor ticks and minor labels.}
    {opt xmtick(numlist)}, {opt ymtick(numlist)}, {opt xmlabel(numlist)},
    {opt ymlabel(numlist)} -- {cmd:dash} does not draw them.  {cmd:xtick()}
    and {cmd:ytick()} are honoured: each adds tick marks without labels
    beside the labels of {cmd:xlabel()} or {cmd:ylabel()}, or the default
    ones, as {cmd:twoway} draws them, and a mark outside the data's range
    widens the axis to show it, as in {cmd:twoway}.

{phang2}{ul:Sizing for graph combine, and scale().}
    {opt fxsize(#)} and {opt fysize(#)} make a graph use only that
    percentage of the width or height it is given -- {cmd:twoway}'s way of
    sizing a panel for {cmd:graph combine}, though they change a graph
    drawn alone too -- and {opt scale(#)} makes all the text, markers and
    lines of a graph larger or smaller.  {cmd:dash} applies none of them:
    a {cmd:dash} figure stretches to the width it is given.  Use
    {cmd:xsize()}, {cmd:ysize()} or {cmd:aspectratio()} to set its
    proportions, and {cmd:layout()} to place it.

{phang2}{ul:Named styles.}
    {opt pstyle(name)}, {opt lstyle(name)}, {opt mstyle(name)},
    {opt mlstyle(name)} -- each names a bundle of settings in a
    {cmd:.scheme} file.  {cmd:dash} reads the scheme's own {cmd:p}{it:#}
    cycles directly; set the properties you want with {cmd:mcolor()},
    {cmd:msymbol()}, {cmd:lcolor()}, {cmd:lpattern()} and {cmd:lwidth()}.
    {cmd:pstyle()} is honoured on {cmd:lfitci}, {cmd:qfitci},
    {cmd:lpolyci} and {cmd:fpfitci}, and not named there (see
    {help dash##ciband:The band's look}).

{phang2}{ul:A confidence band's outline, on other plots.}
    {opt acolor(color)}, {opt alcolor(color)}, {opt alwidth(linewidth)},
    {opt alpattern(linepattern)} -- {cmd:twoway}'s fitarea options.
    {cmd:dash} draws them on the band of {cmd:lfitci}, {cmd:qfitci},
    {cmd:lpolyci} and {cmd:fpfitci}, and does not name them there;
    {cmd:twoway} accepts them on every plot type, and on the others
    {cmd:dash} names them.

{phang2}{ul:A marker's outline pattern, and a label width.}
    {opt mlpattern(linepatternstyle)} -- the pattern of a marker's outline,
    which {cmd:twoway} accepts and {cmd:dash} draws solid.
    {opt mlabwidth(size)} is not a {cmd:twoway} option: {cmd:twoway}
    refuses it, r(198), and {cmd:dash} names it.

{phang2}{ul:colorvar() sub-options.}
    {opt colorlist(colors)}, a colour for each level of {cmd:colorvar()},
    and {opt coloruseplegend}, its keys in a contour-line legend -- both
    Stata 18's; {cmd:dash} colours the levels with {cmd:colpalette()} and
    draws its own key (see
    {help dash##colorvar:Mapping a Variable to Colour}).

{phang2}{ul:Options of other commands.}
    {opt ciopts(...)}, {opt lineopts(...)}, {opt fitopts(...)} --
    {cmd:twoway} refuses all three, r(198): {cmd:ciopts()} belongs to
    commands such as {cmd:marginsplot} and {cmd:sts graph},
    {cmd:lineopts()} to others such as {cmd:stcox}'s diagnostic plots, and
    {cmd:fitopts()} to none of Stata's own.  {cmd:dash} names them and does
    not read their contents; the confidence band, the density line and the
    fitted line keep their default styling.

{phang2}{ul:Orientation, bar labels and positions.}
    {opt horizontal}, {opt vertical} -- {cmd:twoway} draws a bar, spike,
    dropline or range bar sideways with {cmd:horizontal}; {cmd:dash}
    draws every plot upright, bars at the {it:x} variable's values.
    {opt blabel(...)} is {cmd:graph bar}'s and {opt at(varname)} no
    {cmd:twoway} plot's: {cmd:twoway} refuses both, r(198).

{phang2}{ul:Connection order.}
    {opt sort} and {opt sort(varlist)} on every plot type other than
    {cmd:line}, {cmd:connected}, {cmd:area}, {cmd:rline}, {cmd:rarea},
    {cmd:rconnected}, {cmd:tsline} and {cmd:tsrline} -- {cmd:dash} joins no
    points there, and names them in the note.  On the first six they are
    honoured, and {cmd:tsline} and {cmd:tsrline} join in time order, as
    {cmd:twoway} does, so none of the eight names them (see
    {ul:Join order} under the plot types).  A malformed {cmd:sort()} is
    refused on every type, as {cmd:twoway} refuses it.

{phang2}{ul:Marker-label placement and text style.}
    {opt mlabvposition(varname)} -- a layer's labels all sit at the one
    clock position {cmd:mlabposition()} gives; a position per observation
    is not read.  {opt mlabtextstyle(textstyle)} -- a named text style in
    a {cmd:.scheme} file; set the size and colour with {cmd:mlabsize()} and
    {cmd:mlabcolor()}.

{phang2}{ul:Room for long end labels.}
    {opt xoverhangs}, {opt yoverhangs} -- {cmd:twoway} widens the graph
    region so that the label on the first or last tick does not run off the
    edge; {cmd:dash} does not move the figure's edges for them.

{phang2}{ul:Build-time options written on a graph.}
    {opt link(namelist)}, {opt filter(varname, ...)} -- these belong to
    {cmd:dash build} and {cmd:dash serve}, where the link group and the
    filter widgets are made; {cmd:twoway} has neither and refuses both,
    r(198).  Written on a graph they are stored and read by nothing, so
    they are named in the note; give them to {cmd:dash build}.  Stata's
    {cmd:nodraw} is not in this list: written on a graph it is honoured,
    on an immediate render and, once the graph is registered, on
    {cmd:dash build} and {cmd:dash serve} alike, by keeping the browser
    window shut.  {cmd:dash build}'s own option for that is
    {cmd:nobrowser}.

{phang2}{ul:Not drawn.}
    {opt connect(list)} -- use the {cmd:connected} plot type.
    {opt cmissing(y|n)} -- missing observations are dropped before
    rendering, so a line joins the points either side of a gap, which is
    {cmd:twoway}'s default, {cmd:cmissing(y)}; {cmd:cmissing(n)}'s break is
    not drawn.
    {opt recast(plottype)} -- name the plot type you want directly.
    {opt play(recordingname)} -- there is no graph editor to replay.
    {opt text(# # "string")} -- use {cmd:note()} or {cmd:caption()}.

{pstd}
Not in this list, because {cmd:dash} honours them: {cmd:twoway}'s
connecting-line options {cmd:clcolor()}, {cmd:clpattern()} and
{cmd:clwidth()} (abbreviated {cmd:clc()}, {cmd:clp()} and {cmd:clw()}),
which style the line of {cmd:line}, {cmd:connected}, {cmd:lfit},
{cmd:qfit}, {cmd:fpfit}, {cmd:lpoly}, {cmd:lowess}, {cmd:mspline},
{cmd:mband}, {cmd:kdensity}, {cmd:function} and {cmd:tsline}, and the fit
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
{cmd:yalternate} as {cmd:xscale(alt)} and {cmd:yscale(alt)}, whose
{cmd:alt} {cmd:dash} names as a sub-option it does not implement;
{cmd:xcommon} and {cmd:ycommon} are options of {cmd:graph combine};
{cmd:margin()} is a sub-option of {cmd:plotregion()}, {cmd:graphregion()}
and the title options, {cmd:region()} of {cmd:legend()}, and {cmd:altaxis}
of a contour plot's {cmd:clegend()}; {cmd:addplot()} belongs to commands
outside {cmd:graph twoway}, such as {cmd:histogram}; and {cmd:lockaspect},
{cmd:zoom()} and {cmd:ddensity} are options of no Stata graph command.
{cmd:bargap()} is an option of {cmd:graph bar}: {cmd:twoway bar} accepts it
and draws nothing different, and {cmd:dash} names it.

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
below and installs what it can -- the Python packages; a Python you install
and link yourself:

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

{phang2}{ul:Python packages, required} -- bokeh>=3.8, numpy>=2.3,
    pandas>=2.3.

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
    is refused, r(198), naming the variable.  {helpb dash_setup} neither
    checks nor installs it.

{pstd}
On a Python that the operating system manages (PEP 668: Homebrew's, and
recent Debian, Ubuntu and Arch Linux system Pythons), {cmd:dash_setup}
installs nothing and says so; {cmd:dash_setup, venv(}{it:path}{cmd:)} sets
up a private environment instead and prints the {cmd:python set exec} line
that links Stata to it.  See
{help dash_setup##pep668:Externally managed Pythons}.


{marker author}
{title:Also see}

{psee}
{helpb dash_setup}, {helpb twoway}, {helpb python}
