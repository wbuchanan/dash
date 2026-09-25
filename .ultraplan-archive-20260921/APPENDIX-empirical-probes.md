# Empirical twoway-parity probe — live StataNow 19.5, dash @ 3948ce8, 2026-09-18

Method: `dash <spec>, name(gN)` under `capture`, `dash clear` between each. 59 specs.
Result: **22 accepted, 37 rejected.**

## REJECTED — r(198) "option not allowed" (aborts the user's do-file)
xsize() ysize() text() xtick() xmlabel() sort mlwidth() mstyle() lstyle()
horizontal bin() width() percent frequency density start() kernel() n()
level() nodraw play() t1title() b1title() title2() color() blabel()
contour (plottype) pccapsym (plottype)
ABBREVIATIONS: mlab() msym() xlab() mcol() lcol()

## REJECTED — r(101)
function y=x**2, range(0 10)
function y=x**2, n(400)

## ACCEPTED by Stata syntax, but sub-options discarded by the renderer (silent)
title("T", size(large))        -> size() dropped
legend(order(1 2))             -> order() dropped
ylabel(, format(%9.0fc))       -> format() dropped
xlabel(#10)                    -> #N tick-count syntax dropped -> zero ticks
xlabel(minmax)                 -> dropped -> zero ticks
yscale(range(0 50))            -> range() dropped
graphregion(margin(zero))      -> margin() dropped

## ACCEPTED and working (controls)
scatter mpg weight | mc()/ms()/msi() | xla()/xlabel() numeric list | ti()
histogram mpg | kdensity mpg | kdensity mpg, bwidth(2) | lowess, bwidth() | lpoly, degree()
lfitci mpg weight | tsline mpg | scheme() at GRAPH level (not on `dash build`)

## Headline
`dash.sthlp` states that the only unsupported twoway options are `play()` and `nodraw`,
and that specifying them "will produce a warning and the option will be ignored."
Neither string appears anywhere in `dash.ado`, `dash_parse.mata` or `dash_render.py`.
Both abort with r(198). The documented exception list is both wrong and incomplete.

---

# Empirical test 2 — multi-y-variable plots (the `scatter y1 y2 x` form)

Built end to end through live Stata -> jsonio -> dash_render.py -> HTML.

| Command | Series colors found in the generated HTML | Series rendered |
|---|---|---|
| `dash scatter mpg price weight` | `#1a476f` only | **1** |
| `dash (scatter mpg weight) (scatter price weight)` | `#1a476f`, `#90353b` | **2** |

`twoway scatter mpg price weight` draws **two** series (mpg vs weight AND price vs weight).
`dash` draws **one** — `_dash_parse_varpart_std` (`dash.ado:665-670`) takes `yvar = word 1`
and `xvar = last word` and discards everything between. No error, no warning.

This is the single most damaging silent parity break found: the `y1 y2 ... x` form is
everyday `twoway` syntax, and half the user's data vanishes from the chart.

Good news from the same test: the per-series scheme color cycle **does** work for explicitly
overlaid plot specs — `p1` resolved to navy `#1a476f` and `p2` to maroon `#90353b`, matching
s2color. The cycle exists; it is the varlist expansion that is missing.

---

# Empirical test 3 — Stata log pollution on every render

`dash.ado:143` is:

```stata
python: runpy.run_path("`_py_renderpy'", run_name="__main__")
```

A single-line `python:` statement echoes the value of the expression, and `runpy.run_path`
returns the executed module's globals dict. Every `dash build` therefore dumps roughly
10 KB of `dash_render.py`'s module namespace — including its entire docstring — into the
Stata results window and any open log. Assigning the result (`_ = runpy.run_path(...)`)
suppresses it. Contrary to project rule 14 (robust logging without a performance penalty).

---

# Environment note that affects end-to-end verification

`stata-mp` launched normally on this arm64 Mac runs its **x86_64** slice and then fails to
load `/opt/anaconda3/lib/libpython3.13.dylib` (arm64), so `dash build` aborts with r(7100).
Forcing the arm64 slice works:

```bash
arch -arm64 /usr/local/bin/stata-mp -b do <file>.do
```

Stata's `python_exec` is `/opt/anaconda3/bin/python3` (3.13.9), which is a **different**
interpreter from the `/opt/homebrew/bin/python3.14` used by the pytest suite. Any test plan
must pin and verify both, or the Python unit tests and the Stata certification scripts are
exercising different library versions.

---

# Empirical test 4 — `layout(bs)` silently deletes every faceted graph

Two identical dashboards, differing only in the `layout()` value. Both built end to end.

```stata
dash scatter mpg weight, by(foreign) name(f1) title(faceted)
dash scatter price weight,            name(f2) title(plain)
dash build, saving(...) layout(bs)   replace    // vs layout(auto)
```

| Marker searched in the generated HTML | `layout(bs)` | `layout(auto)` |
|---|---|---|
| `faceted` (the by-graph's title) | **absent** | present |
| `plain` (the ordinary graph's title) | present | present |
| `Domestic` (a facet label) | **absent** | present |
| `Foreign` (a facet label) | **absent** | present |

The Bootstrap grid keys cells by graph name and checks `name in self.figures`, but a
faceted graph is stored under the generated keys `name__by__0`, `name__by__1`, ... so the
lookup misses and the graph is dropped from the layout with no error and no warning.

This combines the package's two headline features — the abstract's Bootstrap responsiveness
and `twoway`'s `by()` — and loses one of them silently. Rated BLOCKER.

# Empirical test 5 — figure dimensions

Neither generated file contains a figure `width`, `height` or `frame_width`. Every figure is
emitted with `sizing_mode: "stretch_width"` and Bokeh's built-in default height. `twoway`'s
`xsize()`/`ysize()` are rejected by `dash` (see test 1), and Stata schemes carry
`graphsize 5 / graphsize x 5.5 / graphsize y 4`, which `dash` never reads. There is
currently no way — by option, by scheme, or by data — for a user to influence plot
proportions.

---

# Empirical test 6 — histogram defaults diverge from Stata, badly, and worse as N grows

Stata's own `histogram` chooses bins from the data: k = min(sqrt(N), 10*ln(N)/ln(10)).

| dataset / variable | N | Stata `histogram` default | `dash histogram` |
|---|---|---|---|
| `auto` / `mpg` | 74 | **bin=8**, start=12, width=3.625 | 10 bins |
| `nlsw88` / `wage` | 2,246 | **bin=33**, start=1.0050, width=1.2043 | 10 bins |

`dash_render.py:3001` is `n_bins = min(int(options.get("bin", 10)), _MAX_BINS)`. The literal
`10` applies at every sample size, and `bin()` is rejected by Stata's `syntax`, so the
default is unreachable in practice — it cannot be overridden at all.

Second divergence on the same glyph: `dash_render.py:3003` uses `np.histogram(...)`, which
returns raw **counts**. Stata's `histogram` default y-axis is **density**, and `percent`,
`frequency` and `fraction` are all rejected by `dash`'s `syntax`. So the y-axis is both a
different quantity from Stata's and not selectable.

---

# Empirical test 7 — `dash` is completely non-functional when installed via `net install`

`dash.pkg` declares six files and **omits the `schemes/` directory**:

```
f dash.ado   f dash.sthlp   f dash_setup.ado
f dash_setup.sthlp   f dash_parse.mata   f dash_render.py
```

`SchemeParser._SCHEMES_DIR` (`dash_render.py:702`) is a sibling of `dash_render.py`, so on a
packaged install it does not exist. `DashRenderer.__init__` (`dash_render.py:5002-5004`) is:

```python
try:
    self.scheme = SchemeParser(_scheme_name)
except (ValueError, OSError):
    self.scheme = SchemeParser("s2color")     # <- outside the try
```

The fallback resolves the *same* missing directory and raises the identical `ValueError`,
uncaught.

Reproduced by copying exactly the six files `dash.pkg` lists into a clean directory and
constructing a `DashRenderer` with a minimal spec:

| Install tree | Result |
|---|---|
| Development tree (has `schemes/`) | `DashRenderer` constructed OK |
| `dash.pkg` file set only | `ValueError: dash: scheme 's2color' not found` — **uncaught** |

Every `dash` command would end in a Python traceback for every user who installs the package
the advertised way. It works on the author's machine only because the development tree
contains `schemes/`. Rated BLOCKER, and it is the first thing the plan should fix.
