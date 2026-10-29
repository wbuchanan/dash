# dash: interactive HTML dashboards from twoway syntax

`dash` converts Stata `twoway` plot syntax into interactive dashboards
powered by the Bokeh visualization library: forty-four twoway plot types,
multi-graph layouts, linked brushing, filter widgets
(dropdown/multi/slider/range) and KPI cards. Most twoway options are
honoured; the rest are accepted and named in a note -- see `help dash`,
Unsupported Stata twoway options.

A saved dashboard is one self-contained HTML file, with BokehJS embedded,
that opens in a modern browser without a server or an internet connection.
`dash serve` runs the dashboard on a Bokeh Server instead, and `dash build`
with the `server` option writes such an app for you to launch.

`dash` takes the place of `twoway`: write `dash scatter mpg weight` where
you would write `twoway scatter mpg weight`.  It has been tested on macOS
arm64 with StataNow 19.5, run from the console.

Beyond the graphs, a dashboard can carry:

- several graphs and KPI cards in a `layout()` grid or in `tabs()`;
- filter widgets that every graph and card follows, and link groups whose
  graphs share a box or lasso selection (`link()`, `brush(filter)`);
- KPI cards of a statistic, weighted as `summarize` weights it;
- a folded data table of the rows a graph draws (the `table` graph option)
  and, with `csv`, a Download CSV button;
- PNG and SVG export from the toolbar;
- names for screen readers on every graph, filter, table and card, and
  keyboard-operable tabs.

## Requirements

- Stata 19 or later; tested on StataNow 19.5 (MP), macOS arm64.
  Measured on MP only; Stata 19.0, Stata/BE and Stata/SE have not been run.
  It is run from the console; Windows, Linux, Intel macOS and Stata's graphical interface have not been run.
- Python 3.11+, bokeh>=3.8,<3.10, numpy>=2.3, pandas>=2.3.

## Installation

```stata
net install dash, from("https://wbuchanan.github.io/dash")
dash_setup
```

## dash_setup

Run `dash_setup` once after installation: it checks the dependencies and
installs the missing Python packages; where the Python refuses pip installs
(PEP 668), `dash_setup, venv(path)` sets up a private environment instead.
See `help dash_setup`.

## Example

```stata
sysuse auto, clear
dash (scatter mpg weight) (lfit mpg weight), title("MPG vs Weight") saving(fit.html)
```

## Documentation

- `help dash` -- the syntax, every difference from `twoway`, and the
  dashboard options.
- `help dash_setup` -- installing and checking the Python dependencies.
- [CHANGELOG.md](CHANGELOG.md) -- what changed in each release.

## Support

To report a problem or ask for a feature, file an issue at
<https://github.com/wbuchanan/dash> (the Issues tab), saying which versions
of dash and Stata you run and giving the command that shows the problem.
The maintainer, Billy Buchanan, can be reached at
<william@williambuchanan.net>.
