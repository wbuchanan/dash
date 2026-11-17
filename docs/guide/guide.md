# dash user's guide

This guide shows how to use what `dash` adds to Stata's `twoway`: dashboards of several graphs, KPI cards, filters, data tables, selection and linked brushing, tabs and image panels. Each example is a do-file you can run as it stands, shown above the live dashboard it built, so you can try every feature here as you read about it.

## Before you start

Install `dash` and its Python packages once:

```stata
net install dash, from("https://wbuchanan.github.io/dash")
dash_setup
```

`dash` reads `twoway`'s syntax: write `dash scatter mpg weight` where you would write `twoway scatter mpg weight`, with the same plot types and options. What it draws is an HTML page, which opens in your web browser (`dash` is tested in Google Chrome), not a Stata graph window. `help dash` lists every option and each place where `dash` differs from `twoway`.

The examples use datasets that ship with Stata (`sysuse auto`, `sysuse nlsw88` and `sysuse sp500`). Each writes its page into Stata's working directory and opens it in your browser. To keep the browser shut, for instance in a do-file that builds many dashboards, set `global dash_nobrowser 1`; the page is still written, and `r(filename)` holds its full path.

## One graph or a whole dashboard

`dash` works in two ways. The one-line form draws a single graph straight to a page: `dash scatter mpg weight, saving(scatter.html)`. Without `saving()` it writes a temporary preview page and opens it.

To put several graphs on one page, register each one with `name()`. Nothing is drawn yet: the graph is stored in `dash`'s registry. Then `dash build` writes every registered graph and card to one page. Run `dash clear` before you start a new dashboard, so that graphs from an earlier one are not drawn again.

@example first-dashboard 440

- `dash build` needs `saving()`; add `replace` to overwrite a page that is already there.
- `title()` and `subtitle()` head the page, and `layout()` arranges the graphs (see [Layout and tabs](#layout-and-tabs)).
- A graph's name may be up to 22 characters, without a double underscore; `name(fuel, replace)` registers a graph again under a name already used.

## Reading values: tooltips and hover()

Every graph has tooltips: point at a mark and a box shows the variables the layer plots, each named by its variable label and written in its display format. The `hover()` option, which `twoway` does not have, adds more variables to each tooltip.

@example hover 650

Point at a car: beside its weight and mileage, the tooltip shows its make and model, its price and its origin, named by their variable labels.

`hover()` reaches every layer whose marks are observations: `scatter`, `connected`, `line`, `area`, `bar`, `spike`, and the range and paired-coordinate plot types. A computed layer, such as `lfit`, `lowess`, `kdensity` or `histogram`, draws points that are not observations, so its tooltip shows only what it draws. The hover button on the toolbar turns tooltips off and on.

## The toolbar

Every graph carries the same tools:

- **Pan**: drag to move the graph. This is what a drag does when the page opens.
- **Wheel zoom**: zoom with the mouse wheel or trackpad. It is off when the page opens, so the wheel scrolls the page; click its button to turn it on.
- **Box zoom**: drag a rectangle to zoom to it.
- **Box select** and **Lasso select**: drag a rectangle, or draw around points, to select them. See [Selecting and linked brushing](#selecting-and-linked-brushing).
- **Undo** and **Redo**: step back and forward through your pans, zooms and selections.
- **Reset**: return the axes to where the last filter move left them, and clear the selection.
- **Save**: write the graphs as a PNG image.
- **Save as SVG** and **Save dashboard**: write the whole dashboard, with its title, filters and KPI cards, as a vector SVG file or a PNG image.

The graphs of a grid share one toolbar, above the grid, which appears when the pointer is over the grid. A tool chosen there acts on every graph in the grid, and Undo, Redo and Reset act on all of them at once. Under `layout(bs)` each graph has its own toolbar beside it, always shown. Each tab of `tabs()`, and the panels of a `by()` graph, have a toolbar of their own.

## Selecting and linked brushing

Choose **Box select** or **Lasso select** and drag across a graph: the points inside are selected, and the others are drawn faint.

`link()` on `dash build` puts graphs in a link group. The graphs of a group draw their observations from one shared copy of the data, so a selection on any one of them selects the same observations on every other. This is linked brushing: pick out the heaviest cars on one graph and see where they fall on the others.

@example linked 340

Try it:

- Move the pointer over the graphs to show the toolbar, choose **Box select**, and drag a rectangle around the heaviest cars on the left graph. The same cars stay bright on the middle graph, and the rest fade.
- Drag a rectangle across one bar of the histogram. The cars that bar counts are selected on both scatter plots.
- Click **Reset** to clear the selection.

A selection shows on the layers drawn as markers: `scatter`, `connected` and `dot`, and the markers of `rspike` and `rconnected`. Lines, areas, bars, fits, smoothers, densities and histograms are drawn from data of their own and do not show a selection, though, as above, selecting a histogram's bars selects the observations they count.

- `link(_all)` links every registered graph.
- `link()` may be given more than once. Each copy is a separate group, and a selection in one group does not reach the other: `link(g1 g2) link(g3 g4)`.
- Each graph keeps its own `if` and `in`. A graph drawn `if foreign == 1` shows only the foreign cars of a selection made on a graph of every car.
- A graph that is in no link group is not affected by selections on the others.

### Brushing that filters

By default a selection draws the observations it leaves out faint (`brush(highlight)`). With `brush(filter)` it hides them instead: on the graph you brushed, on the other graphs of its group, and in a linked graph's data table. Clearing the selection shows every observation again.

@example brush-filter 520

Select a group of cars on either graph: the other graph shows only those cars, **Cars selected** counts them and **Mean price** averages their prices. Click **Reset** to bring every car back.

Under `brush(filter)` every KPI card follows the selection. Under the default `brush(highlight)`, a card follows selections when it is registered with `update(brush)` or `update(both)`. Selections on several graphs act together: a card counts the observations that every current selection holds.

## KPI cards

A KPI card shows one statistic in large type. `dash kpi` registers one, to be placed by `dash build` beside the graphs:

```stata
dash kpi mean(price), title("Mean price") name(p) fmt(%9.0fc)
```

The statistic is one of `mean`, `sum`, `count` (non-missing values), `dcount` (distinct non-missing values), `min`, `max`, `median`, `sd`, `var`, `cv`, `iqr`, `skewness`, `kurtosis`, `semean` and `range`, or any percentile, written `p25`, `p90` or `p97.5`. Each is the number `summarize, detail` reports: percentiles follow Stata's own rule, and the variance divides by N-1. `count` and `dcount` also take a string variable.

- `title()` and `name()` are required. A card's name may be up to 18 characters.
- `fmt()` is a numeric display format, such as `%9.2f` or `%12.0fc`, or a date format. Without it the card uses the variable's own display format.
- `subtitle()` adds smaller text under the value.
- `color()` and `bgcolor()` set the value's colour and the card's background, as Stata colour names or hex codes.
- `update()` says what the card follows: `filter` (the default) recomputes it when a filter moves, `brush` when a selection changes, and `both` on either.
- `if`, `in` and weights work as for `summarize`: `aweight`, `fweight` and `iweight` are allowed, and the card stays weighted after every filter move and selection.

A card is one statistic over the rows its `if` and `in` select. For a statistic of each group, register a card for each, such as `dash kpi mean(mpg) if foreign == 0, title("Domestic") name(kdom)`.

@example kpi 910

Choose **Black** in the **Race** filter: every card recomputes over the 583 women the filter leaves, and the scatter plot shows only them. Choose **All**, or click **Reset filters**, to bring every woman back.

## Filters

`filter()` on `dash build` adds a widget above the dashboard that keeps some observations and drops the rest, on every graph and KPI card. Give `filter()` once for each widget, up to 20. Its `type()` is one of four:

- `dropdown`, the default: pick one value, or **All**. When the variable has missing values, a **(missing)** entry keeps just those. Values are shown in the variable's display format or value labels.
- `multi`: pick several values; with none picked, every observation is kept.
- `slider`: keep the observations at or above the slider's value.
- `range`: keep the observations between the two handles, both included.

A slider or range recomputes the dashboard when you let go of it. Once moved, it drops the observations whose value is missing.

- `exclude()` names graphs and KPI cards that the filter leaves alone.
- `label()` sets the widget's text; without it, the widget shows the variable's label, or its name.
- `direction(rtl)` runs a slider or range from right to left.
- A **Reset filters** button puts every widget back where it started.
- `filterposition(left)` on `dash build` puts the widgets in a sidebar beside the dashboard, instead of a row above it, as in the example below.

The graphs of a link group draw from one copy of the data, so a filter moves the whole group, unless it excludes every graph in it.

@example filters 470

Try it:

- Drag **Years of school, at least** to 16 and let go: **Mean wage** rises from 7.77 to 10.48, but **Women in the data** stays at 2,246, because that filter excludes the card.
- Pick **Black** in **Race**: both cards change, since the race filter excludes neither.
- Drag a handle of the **Age** range, or pick occupations in **Occupation**.

## Data tables and downloads

`table` is a graph option of `dash`'s own. It puts a **Data table** button under the graph, and behind it a table of the observations the graph draws, folded away until you press the button. `table(rows(#) open)` lists at most # rows (the default is 1,000) and opens the table when the page opens.

The table's columns are the variables the graph plots, then its `hover()` variables, each headed by its variable label, with every value written as Stata displays it. Click a heading to sort by that column. The table follows every filter move, and, under `brush(filter)`, a linked graph's table lists just the selected rows.

`csv` on `dash build` adds a **Download CSV** button. It downloads `dashboard.csv`: every observation the filters leave, with a column for each variable the dashboard uses, written as `export delimited` writes it (dates in ISO 8601). Only the filters count; a selection and a graph's own `if` and `in` do not.

@example tables 1360

Choose **Foreign** in **Car origin**: the table drops to the 22 foreign cars. Click **Download CSV** to save them, or click a heading to sort the table.

`csv` is off unless you ask for it. Without it, a page holds only the observations its graphs, cards and filters use; with it, the page holds every observation of every variable it uses, so that anyone who opens the page can download them.

## Layout and tabs

`layout()` on `dash build` arranges the graphs, KPI cards and image panels:

- `layout(auto)`, the default, picks a square-ish grid from the number of items: four make a 2 x 2 grid.
- `layout(2 3)` asks for 2 rows and 3 columns, filled row by row.
- `layout(s1:1,1 s2:1,2 k1:2,1)` places each named item at a row and column.
- `layout(bs: k1=3 k2=3 s1=6)` uses a 12-column grid: each name takes the number of columns given, and `/` starts a new row. The KPI and filter examples above use it.

On a narrow window or a phone, a grid stacks its items into one column, and no dashboard scrolls sideways.

`tabs()` groups items into tabs, written as a title, a colon and the names in it, with `/` between tabs: `tabs(Overview: k1 s1 / Detail: s2 h1)`. A tab may end with its own `, layout()`. An item named in no tab is drawn below the tabs. The tabs work from the keyboard: Tab moves to them, the arrow keys move between them, and Enter or Space opens one.

@example tabs 560

Open the **Detail** tab to see the other two graphs.

## Image panels

`dash image using` registers an SVG picture, which `layout()` and `tabs()` place by its name as they place a graph: a logo, a diagram, or a graph Stata drew, exported with `graph export`. `caption()` is shown beneath it, and `alt()` is its text for a screen reader.

@example image-panel 430

The file must be well-formed SVG, with no script and nothing loaded from outside it. `link(page.html)` makes the picture a link to another page in the same folder.

## Graphs from several frames

A graph is drawn from the frame it was registered in, so one `dash build` can hold graphs of several datasets. Register each with Stata's own `frame` prefix, as you would draw it with `twoway`.

@example frames 400

KPI cards read the frame that is current when `dash build` runs. A filter acts on the graphs whose frame holds its variable. A link group cannot join graphs from two frames.

## Themes and schemes

A dashboard takes the session's graph scheme, `c(scheme)`, so it looks like the other graphs you draw. `scheme()` on `dash build` applies another Stata scheme to the whole dashboard, and `theme()` is a short name for one: `default`, `clean`, `mono`, `dark`, `economist` or `sj`. `scheme()` wins when both are given. A `scheme()` written on one graph draws that graph alone in it.

## Saving, sharing and printing

- A saved dashboard is one HTML file holding everything it needs. It opens offline, with no server or internet connection, so you can send it by email or put it on a website as it stands.
- A page holds only the observations some graph, KPI card or filter uses, after their `if` and `in`. Anyone who opens it can read them with the browser's View Source; with `csv`, it holds every observation of every variable it uses.
- A page can be shown inside another web page with an `<iframe>`, as this guide shows its examples.
- `graph export` cannot write a dashboard, which is drawn in the browser. Use the toolbar's **Save**, **Save as SVG** and **Save dashboard** buttons.
- Printing a dashboard from the browser prints it without the toolbars and filters. With `tabs()`, each tab prints on a page of its own.

## Live dashboards with dash serve

`dash serve` runs the dashboard on a Bokeh Server on your machine instead of writing a file, and Stata waits until you press Break. Moving a filter makes the server recompute every layer computed from the data, such as a histogram's bins, a fitted line or a smoother, and every KPI card that follows the filters. It takes `dash build`'s options, and reuses those of the last `dash build` that you do not restate:

```stata
sysuse auto, clear
dash clear
dash scatter mpg weight, name(s1) title("MPG vs Weight")
dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f)
dash build, saving(dashboard.html, replace) filter(foreign)
dash serve, port(5006)
```

The served dashboard opens only through a link that holds a key made for each launch. `dash build, server` writes the app as a `.py` file instead, to run outside Stata with `python app.py`. A served dashboard cannot be shown on this site, which holds only saved pages. A saved page recomputes its KPI cards, kernel densities, histogram heights and fitted and smoothed lines in the browser as filters move.

## Accessibility

- Every graph, filter, button, data table and KPI card is named for screen readers, a graph by its title.
- The tabs of `tabs()` work from the keyboard.
- Every scheme `dash` ships meets the WCAG AA contrast ratio of 4.5:1 for its text; colours you give in options are not checked.

## Where to read more

- `help dash` in Stata: the full syntax, every option, and the differences from `twoway`.
- [The gallery](https://wbuchanan.github.io/dash/gallery/): Stata's `twoway` graph beside `dash`'s for hundreds of examples.
- To report a problem or ask for a feature, file an issue at <https://github.com/wbuchanan/dash>.
