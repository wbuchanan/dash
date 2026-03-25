# Development Plan: `dash` — Multi-Graph Interactive Dashboards from Stata `twoway` Syntax

---

## Context

The `dash` command aims to be a drop-in replacement for Stata's `twoway` that produces interactive HTML dashboards instead of static graphs. The original plan covered single-graph output. This update expands the scope to support **multi-graph dashboards** with linked brushing, cross-graph filtering, KPI cards, and metadata-rich data sharing via `jsonio`. The motivation is to give Stata researchers a zero-server, zero-JavaScript interactive dashboard tool that reuses the syntax they already know.

---

## 1. Architecture Decision: Bokeh

**Bokeh is the chosen library.** The multi-graph dashboard requirements widen the gap over Altair decisively:

| Criterion | Bokeh | Altair |
|---|---|---|
| Linked brushing | Automatic via shared `ColumnDataSource` | Requires explicit selection bindings |
| Filter exclusion per graph | Native `CDSView` model | Awkward selective `transform_filter` |
| KPI cards | `Div` widget — native HTML/CSS | No native component; workarounds |
| Layout flexibility | `gridplot`/`row`/`column`/`layout` | `hconcat`/`vconcat` only |
| Standalone HTML | `CustomJS` required for widgets | Native — all interactions work |
| Glyph model ↔ `twoway` | 1:1 mapping | Requires mark abstraction |
| Widget variety | Full suite (Select, Slider, RangeSlider, etc.) | Limited binding types |

**Bokeh's `CustomJS` limitation is mitigated**: all required interactions (brushing, filter dropdowns/sliders, KPI updates) work in standalone HTML via `CustomJS`. The Python renderer generates all JavaScript programmatically — users never write a line of JS.

---

## 2. Syntax Specification

### 2.1 Single-Graph (immediate render)

```stata
dash (scatter mpg weight, mcolor(red)) (lfit mpg weight), title("MPG vs Weight") saving(out.html)
```

### 2.2 Multi-Graph Dashboard (accumulate + build)

```stata
* Define graphs
dash (scatter mpg weight, mc(red)) (lfit mpg weight), name(s1) title("MPG vs Weight")
dash (scatter mpg length), name(s2) title("MPG vs Length")
dash (histogram mpg, bin(20)), name(h1) title("MPG Distribution")

* Define KPI cards
dash kpi mean(mpg), title("Average MPG") name(k1) fmt(%9.1f)
dash kpi dcount(rep78), title("Repair Categories") name(k2) fmt(%9.0f) update(both)

* Build the dashboard
dash build, saving(dashboard.html) title("Auto Dashboard")  ///
    layout(2 2) link(s1 s2)                                  ///
    filter(foreign, type(dropdown) exclude(k1))               ///
    filter(weight, type(range) exclude(k2))                   ///
    theme(clean) replace
```

### 2.3 Formal Grammar

```
Single graph (immediate render):
    dash <plot_specs> [if] [in], <graph_options> [saving(filepath[, replace])]

Named graph (accumulate for dashboard):
    dash <plot_specs> [if] [in], <graph_options> name(identifier[, replace])

KPI card:
    dash kpi <statistic>(varname) [if] [in],
        title(string) name(identifier)
        [fmt(format)] [subtitle(string)] [icon(string)]
        [color(color)] [bgcolor(color)]
        [update(filter|brush|both)]

Build dashboard:
    dash build, saving(filepath) [title(string)] [subtitle(string)]
        [layout(rows cols | auto)]
        [link(name1 name2 [name3 ...] | _all)]
        [filter(varname, type(dropdown|slider|range) [exclude(name1 [name2 ...])])]
        [theme(theme_name)]
        [replace]

Clear registry:
    dash clear

Setup:
    dash_setup
```

Where:
- `<plot_specs>` = `(plottype varlist, options) [(plottype varlist, options) ...]` or `plottype varlist [|| plottype varlist]`
- `<statistic>` = `mean | sum | count | dcount | min | max | median | sd | p25 | p50 | p75`
  - `dcount` = distinct count, computed via `codebook`
- `<identifier>` = Stata name (letter/underscore + alphanumeric, up to 32 chars)

### 2.4 The `name()` Option — Triple Purpose

1. **Graph registration**: Associates the plot spec with an ID stored in `$dash_graph_registry` (semicolon-delimited). Each graph's spec in `$dash_spec_<name>`, options in `$dash_opts_<name>`.
2. **Layout placement**: Graphs placed in grid order of registration. Explicit placement also supported: `layout(s1:1,1 s2:1,2 k1:2,1)`.
3. **Interaction targeting**: `link(s1 s2)` and `filter(..., exclude(k1))` reference graphs by name.

The `replace` sub-option allows redefining a previously named graph without error.

### 2.5 Brushing and Linking

```stata
dash build, saving(out.html) link(s1 s2)   // two graphs share selection
dash build, saving(out.html) link(_all)     // all graphs share selection
```

All graphs in `link()` share one `ColumnDataSource`. Selection propagates automatically. A **single link group** per dashboard is supported. Graphs outside the group get independent sources.

### 2.6 Cross-Graph Filtering

```stata
filter(foreign, type(dropdown))                         // affects all
filter(foreign, type(dropdown) exclude(k1 k2))          // skip KPIs
filter(weight, type(range) exclude(s2))                 // skip one graph
```

Each filter creates a Bokeh widget + `CustomJS` that applies a `BooleanFilter` to each non-excluded graph's `CDSView` and updates KPI `Div` values.

### 2.7 KPI Cards

```stata
dash kpi mean(mpg),   title("Average MPG") name(k1) fmt(%9.1f) update(filter)
dash kpi dcount(rep78), title("Repair Types") name(k2) fmt(%9.0f) update(both)
dash kpi count(mpg),  title("N") name(k3) color(white) bgcolor(#2c3e50)
```

**Update modes:**
- `update(filter)` *(default)* — recalculates when filter widgets change
- `update(brush)` — recalculates when data is selected via brushing
- `update(both)` — recalculates on either

---

## 3. User Stories

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-1 | Replace `twoway` with `dash` for a single scatter | Standalone HTML with hover tooltips, pan/zoom; works offline |
| US-2 | Overlay scatter + fit line | Both layers on same figure; legend distinguishes them |
| US-3 | Multiple graphs on one page | `dash` + `dash build` → single HTML; `layout()` controls grid |
| US-4 | Linked brushing | `link(s1 s2)` — select in A highlights same obs in B |
| US-5 | Cross-graph dropdown filter | `filter(foreign, type(dropdown))` — all graphs update; `exclude()` skips named graphs |
| US-6 | KPI cards | `dash kpi mean(mpg)` → styled card; updates with filters unless excluded |
| US-7 | Metadata-rich labels | Variable labels → axis titles; value labels → tick labels, dropdowns |
| US-8 | If/in qualification | `dash scatter y x if foreign==1` renders only matching obs |

---

## 4. Business Requirements

| ID | Requirement |
|---|---|
| BR-1 | Drop-in `twoway` replacement for supported plot types |
| BR-2 | Zero server — standalone HTML, works offline in any modern browser |
| BR-3 | Metadata fidelity — variable/value labels used throughout |
| BR-4 | Graceful dependency management with clear error messages |
| BR-5 | 100K observations renders < 30s; smooth interaction up to 50K points (WebGL) |
| BR-6 | All user input sanitized; no injection into Python or JavaScript contexts |

---

## 5. Technical Requirements

### TR-1: `dash.ado` — Stata Entry Point

**Responsibilities:** Route subcommands (plot, `kpi`, `build`, `clear`); capture raw syntax via `` `0' ``; validate and store in global registry; orchestrate jsonio + Mata parser + Python renderer on `build`.

**Registry globals:**
- `$dash_graph_registry` — semicolon-delimited ordered name list
- `$dash_spec_<name>` — raw plot syntax
- `$dash_opts_<name>` — graph-level options
- `$dash_kpi_<name>` — KPI definition (stat, var, value, fmt, title, subtitle, colors, update mode)

**Input validation:**
- `name()`: `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$`
- File paths: no `..` traversal; `confirm new file` / `confirm file` with replace
- All strings: UTF-8 validated before passing to Python
- Option values: HTML-escaped before embedding in output

### TR-2: `dash_parse.mata` — Two-Pass Mata Parser

**Pass 1 — Tokenization:** Character-by-character scan; tracks parenthesis depth; respects `"..."` and `` `"..."' `` quotes; comma at depth 0 = scope delimiter. Token types: OPEN_PAREN, CLOSE_PAREN, WORD, COMMA, PIPE_PIPE, QUOTED_STRING.

**Pass 2 — Structural parsing:** Groups tokens into plot specs (top-level `()` groups or `||` segments); extracts plot type, varlist, options per spec; remaining tokens after final top-level comma = graph-level options.

**Abbreviation expansion:** Mata associative array — `mc`→`mcolor`, `ms`→`msymbol`, `lc`→`lcolor`, `lw`→`lwidth`, `ti`→`title`, etc. Shortest unique prefix rule.

**JSON output per graph:**
```json
{
  "plots": [
    {"type": "scatter", "yvar": "mpg", "xvar": "weight", "options": {"mcolor": "red"}},
    {"type": "lfit",    "yvar": "mpg", "xvar": "weight", "options": {"lcolor": "blue"}}
  ],
  "graph_options": {"title": "MPG vs Weight", "name": "s1"}
}
```

### TR-3: `dash_render.py` — Python/Bokeh Rendering Engine

**Classes:**
```python
class DashRenderer:       # orchestrator → standalone HTML
class GlyphMapper:        # Stata plot type → Bokeh glyph (one method per type)
class OptionTranslator:   # Stata option values → Bokeh properties
class FilterBuilder:      # filter widgets + CustomJS callbacks
```

**Linked brushing:** Graphs in `link()` share one `ColumnDataSource`; Bokeh propagates selection automatically. Non-selected points at `nonselection_alpha=0.15`.

**Filtering:** Each widget gets `CustomJS` applying `BooleanFilter` to `CDSView` on non-excluded graphs; KPI `Div.text` updated by recomputing aggregate from filtered source data.

**KPI cards:** Bokeh `Div` with styled HTML (title, large value, subtitle). `CustomJS` listeners attached per `update()` mode: filter-mode on widget `value`, brush-mode on `source.selected.indices`, both-mode on both.

### TR-4: jsonio Integration

`dash build` serializes the union of all required variables via:
```stata
jsonio out `all_vars' `if_cond' `in_cond', what(all) ///
    filenm("`tmpdir'/dash_data.json")                ///
    metaprint(varnames varlabels vallabs labelnames)
```

Python reads the `StataJSON` envelope: `variableLabels` → axis titles, `valueLabels` → tick labels/dropdowns/legend, `variableTypeIsString` → dtype handling, `values` → `ColumnDataSource` data.

`dash_setup` auto-installs jsonio via `ssc install jsonio` if missing. jsonio is a hard requirement (no CSV fallback).

### TR-5: `dash_setup.ado`

Checks and auto-installs: Python (`python query`), packages bokeh/numpy/scipy/statsmodels/pandas with minimum versions, jsonio (`which jsonio` → `ssc install jsonio`). Reports status per dependency.

---

## 6. File Structure

```
dash/
├── dash.ado                   # Subcommand routing, registry, jsonio call, Python dispatch
├── dash_parse.mata            # Tokenizer + structural parser + abbreviation expansion
├── dash_render.py             # Bokeh renderer: DashRenderer, GlyphMapper, OptionTranslator, FilterBuilder
├── dash_setup.ado             # Dependency installer
├── dash.sthlp                 # SMCL help file (redirects to twoway docs; focuses on differences)
├── dash_setup.sthlp           # SMCL help for setup
├── test/
│   ├── test_tokenizer.cscript     # Tokenizer certification script
│   ├── test_parser.cscript        # Parser certification script
│   ├── test_glyphs.py             # Glyph mapper unit tests (pytest)
│   ├── test_options.py            # Option translator unit tests (pytest)
│   ├── test_layout.py             # Layout assembly tests (pytest)
│   ├── test_filters.py            # Filter widget + CustomJS tests (pytest)
│   ├── test_kpi.py                # KPI computation + rendering tests (pytest)
│   ├── test_linking.py            # Linked brushing tests (pytest)
│   ├── test_jsonio.cscript        # jsonio integration certification script
│   ├── test_e2e_single.cscript    # E2E: single graph
│   ├── test_e2e_multi.cscript     # E2E: multi-graph dashboard
│   ├── test_e2e_filters.cscript   # E2E: filter widgets
│   ├── test_e2e_kpi.cscript       # E2E: KPI cards
│   └── test_adversarial.cscript   # XSS, injection, path traversal, exhaustion
└── examples/
    ├── basic_scatter.do
    ├── multi_graph_dashboard.do
    └── full_dashboard.do
```

---

## 7. Phased Development Roadmap

### Phase 1: Foundation + Multi-Graph (Weeks 1–12)

**Subphase 1A — Core Infrastructure (Weeks 1–4):**
- `dash.ado`: full subcommand routing, global registry, `name()`, single-graph and accumulate/build modes
- `dash_parse.mata`: tokenizer + parser for `()` and `||` syntax
- `dash_render.py`: `DashRenderer` + `GlyphMapper` for `scatter`, `line`, `connected`, `area`, `bar`, `spike`
- `OptionTranslator` for `mcolor`, `msymbol`, `msize`, `lcolor`, `lwidth`, `lpattern`, `title`, `xtitle`, `ytitle`, `xlabel`, `ylabel`, `xscale(log)`, `yscale(log)`, `xline`, `yline`
- jsonio integration; `dash_setup.ado` with auto-install
- Hover tooltips; `saving()` option; input validation + UTF-8 + HTML escaping
- `.cscript` tests for tokenizer, parser; pytest for glyph mappers, option translators

**Subphase 1B — Multi-Graph & Linking (Weeks 5–8):**
- `dash build` with `layout(rows cols)` and `layout(auto)` via `gridplot`
- Linked brushing: shared `ColumnDataSource` + `link()` option (single group)
- `dash clear`; `if`/`in` support; abbreviation expansion engine; `legend()` option
- Plot types: `lfit`, `qfit`, `lfitci`, `qfitci`, `lowess`, `histogram`, `kdensity`
- `.cscript` tests for multi-graph/linking; pytest for layout, new plot types

**Subphase 1C — By-groups & Polish (Weeks 9–12):**
- `by()` → Bokeh `gridplot` small multiples
- Responsive layout (`sizing_mode="stretch_width"`)
- `dash.sthlp` initial version; E2E certification scripts; error message refinement

### Phase 2: Filters, KPIs, Advanced Interaction (Weeks 13–20)

- `dash kpi` with `update(filter|brush|both)` option; `dcount` via `codebook`
- `FilterBuilder`: dropdown, slider, range filter types; `filter()` with `exclude()`
- KPI `Div` widgets with `CustomJS` update callbacks
- Range plots: `rarea`, `rbar`, `rspike`, `rcap`, `rline`, `rconnected`; `dot` plot type
- Dashboard `theme()` option; WebGL for datasets > 10K points
- Comprehensive E2E + adversarial certification scripts (CLAUDE.md rule 18)

### Phase 3: Polish & Distribution (Weeks 21–28)

- Complete `dash.sthlp` + `dash_setup.sthlp`
- `scheme()` translation for `s2color`, `plotplain`
- `dash export, format(png|svg)` via Bokeh export
- Package files (`dash.pkg`, `stata.toc`) for SSC
- Performance benchmarks (100K obs < 30s); security audit (CLAUDE.md rule 13)

---

## 8. Test Plan

### Certification Scripts (Stata) and Unit Tests (Python)

All Stata-side tests use `.cscript`. Python-side tests use `pytest`.

| File | Coverage |
|---|---|
| `test_tokenizer.cscript` | Single word, quoted strings, nested parens, depth tracking, `\|\|`, empty input, long strings, unicode, unbalanced parens |
| `test_parser.cscript` | Single/multi-layer, `\|\|`, abbreviation expansion, `name()`, `if`/`in`, invalid plot type, injection attempts |
| `test_glyphs.py` | Each plot type → correct glyph; lfit coefficients; histogram bins; missing data excluded |
| `test_options.py` | Every Stata color → hex; markers; size keywords; invalid values → errors |
| `test_layout.py` | 2×2 grid; auto-layout; empty cells; KPIs in grid; responsive sizing |
| `test_filters.py` | Dropdown/slider/range CustomJS; exclude list honored; value labels in dropdowns |
| `test_kpi.py` | All stat functions incl. `dcount`; format applied; Div HTML; `update()` modes generate correct listeners |
| `test_linking.py` | Linked graphs share source; non-linked independent; single group enforced |
| `test_jsonio.cscript` | var/value labels present; data matches; `if` qualifier; missing values handled |

### End-to-End Certification Scripts

| File | Scenario |
|---|---|
| `test_e2e_single.cscript` | `dash scatter mpg weight, saving(test.html)` → HTML with Bokeh elements |
| `test_e2e_multi.cscript` | 3 named graphs + `dash build` → HTML contains all 3 graph IDs |
| `test_e2e_filters.cscript` | Dropdown on `foreign` → Select widget with "Domestic"/"Foreign" |
| `test_e2e_kpi.cscript` | `dash kpi mean(mpg)` → HTML contains computed mean value |

### Adversarial Tests (CLAUDE.md Rule 18)

| Attack | Vector |
|---|---|
| XSS | `title("<script>alert(1)</script>")` → escaped in output HTML |
| Shell injection | Variable name with metacharacters → no execution |
| Path traversal | `saving("../../../etc/passwd")` → rejected |
| Python injection | `mcolor("red"); import os; os.system(...)` → treated as literal |
| Resource exhaustion | 1000+ variable names → graceful error |
| Stack overflow | 100+ nested parentheses → graceful error |

---

## 9. Security Considerations

1. **Variable names**: validated against `[a-zA-Z0-9_]` before passing to Python
2. **String values**: HTML-escaped before embedding in Div/title/CustomJS
3. **File paths**: no `..`; must end in `.html`; validated with `confirm new file`/`confirm file`
4. **No eval/exec**: renderer uses `json.loads()` + expected-key access only
5. **CustomJS safety**: parameterized templates — no string interpolation of user values into JS
6. **UTF-8 enforcement**: Mata parser rejects non-UTF-8 bytes
7. **CSP meta tag**: output HTML restricts scripts to inline only

---

## 10. Data Flow Summary

```
dash (scatter mpg weight) (lfit mpg weight), name(s1) title("T")
    → stores spec in $dash_spec_s1, appends "s1" to $dash_graph_registry

dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f)
    → computes mean via summarize, stores in $dash_kpi_k1

dash build, saving(out.html) layout(2 1) link(s1 s2) filter(foreign, type(dropdown))
    → dash.ado:
        1. Union of all variables across specs + KPIs
        2. jsonio out vars, what(all) filenm(tmpdir/data.json) metaprint(...)
        3. For each name: dash_parse.mata → per-graph JSON
        4. Assembles master JSON (all graphs + KPIs + build options)
        5. python: DashRenderer(master.json, data.json).render()
    → dash_render.py:
        1. Load jsonio JSON → ColumnDataSource (shared for linked graphs)
        2. Build Bokeh Figure per graph; GlyphMapper per plot layer
        3. Build KPI Divs; FilterBuilder for widgets + CustomJS
        4. gridplot/row/column layout assembly
        5. bokeh.io.save() → standalone HTML
    → HTML opens in browser
```

---

## 11. SMCL Help File Design

**Principle**: Redirect to existing Stata `twoway` documentation; document only what `dash` adds or changes.

```smcl
{vieweralsosee "twoway"        "mansection G-2 graphtwoway"}
{vieweralsosee "twoway scatter" "help scatter"}
{vieweralsosee "twoway line"    "help line"}
{vieweralsosee "twoway lfit"    "help twoway_lfit"}
... (one vieweralsosee per supported plot type)

Sections (in order):
  Syntax          — all 4 forms (single, named, kpi, build)
  Description     — brief; links to {manhelp twoway G-2} for full syntax
  Differences from twoway — focused: interactive HTML output; name() repurposed;
                             new subcommands (kpi, build, clear);
                             new options (link, filter, layout, theme, update);
                             unsupported twoway features with Phase timelines
  Dashboard Options — synoptset for dash build options only
  Plot options    — cross-reference table pointing to existing Stata help
  KPI Cards       — full documentation (no twoway equivalent)
  Examples        — basic scatter → full multi-graph dashboard
  Dependencies    — dash_setup usage
  Author
```

---

## 12. Verification Plan

1. **Subphase 1A**: `sysuse auto; dash scatter mpg weight, saving(test.html)` → HTML opens with tooltips and zoom
2. **Subphase 1B**: 3 named graphs + `dash build, link(s1 s2)` → all 3 in layout; select in s1 highlights s2
3. **Phase 2**: Add KPI + dropdown filter → filter change updates non-excluded graphs; KPI recalculates
4. **All phases**: Run `test/*.cscript` (certification scripts) + `pytest test/` before every commit

---

## Phase 4: Bokeh Server Mode — `dash serve` (Weeks 29–38)

### Overview

Phase 4 adds a live Bokeh Server rendering path that keeps Python running while
the user interacts with the dashboard.  This eliminates all three limitations of
standalone HTML: KPI cards recompute dynamically on any filter/brush event;
aggregated plot types (histogram, lfit, kdensity, qfit) recompute bins and
coefficients when filters change; and all chart types participate fully in
cross-filter interactions.

The core deliverable is a new `dash serve` subcommand and an optional `server`
flag on `dash build`.  Both paths share the existing parser, jsonio integration,
and registry — only the final rendering step changes.

---

### 4.1 User Stories

| ID | Story | Acceptance Criteria |
|---|---|---|
| US-9  | Live interactive dashboard | `dash serve` registers graphs, launches browser, KPI tiles recompute instantly on filter change |
| US-10 | Histogram updates on filter | Select "Foreign" in dropdown → histogram bins recompute from filtered rows |
| US-11 | All plot types brush-linkable | lfit line recomputes slope from selected points after brush selection |
| US-12 | Deployable server app file | `dash build, saving(app.py) server` → standalone `.py` file runnable with `bokeh serve app.py` |
| US-13 | Server stops cleanly | Press Ctrl+C → server shuts down gracefully; Stata returns to prompt |
| US-14 | Port is configurable | `dash serve, port(8080)` launches on port 8080 instead of default 5006 |
| US-15 | Auto-timeout option | `dash serve, timeout(30)` stops server after 30 minutes automatically |

---

### 4.2 Business Requirements

| ID | Requirement |
|---|---|
| BR-7 | `dash serve` blocks Stata while the server is running — this is the expected behavior |
| BR-8 | `dash build, saving(app.py) server` is non-blocking — writes app file, displays run instruction |
| BR-9 | Generated `.py` app file is self-contained — no external file path dependencies at runtime |
| BR-10 | Server mode enables full dynamic KPI recomputation for all supported statistics |
| BR-11 | All aggregated plot types (histogram, lfit, qfit, kdensity, lowess) recompute on filter change |
| BR-12 | WebSocket connections restricted to `localhost:{port}` to prevent cross-origin access |
| BR-13 | Generated app is syntactically valid Python, importable for testing without launching a server |

---

### 4.3 Technical Requirements

#### TR-6: `dash.ado` — `serve` Subcommand

**New subcommand routing:** detect `serve` as first token; route to `_dash_serve`.

**`_dash_serve` program:**
- Options: `port(string)` (default 5006), `nobrowser`, `timeout(string)` (minutes, default 0)
- Validates port is integer in range 1024–65535
- Validates timeout is non-negative integer
- Requires registry non-empty
- Serializes all registered variables via jsonio (identical logic to `_dash_build`)
- Assembles master JSON with `"mode":"server"` in `build_options`
- Calls `dash_render.py --mode server` via `python:` block to generate a temp `.py` app file
- Launches Bokeh Server from second `python:` block using `bokeh.server.server.Server`
- Displays URL and stop instructions before blocking
- Handles timeout via `tornado.ioloop.IOLoop.call_later()` when `timeout() > 0`
- Catches shutdown cleanly; displays "Server stopped" on return

**`_dash_build` `SERVER` option:**
- When `server` option present, output path must end in `.py` not `.html`
- Calls `dash_render.py --mode server` instead of `--mode standalone`
- Non-blocking; displays `bokeh serve <file>` instructions after writing app file

#### TR-7: `dash_render.py` — Argparse + `--mode server` Flag

**CLI interface update:**
- Replace positional-arg `__main__` block with `argparse`
- Required flags: `--spec`, `--data`, `--output`
- Optional flag: `--mode` (values: `standalone`, `server`; default `standalone`)
- `main()` updated to accept and dispatch on `mode` parameter

**`ServerAppBuilder` class:**

```
ServerAppBuilder
    __init__(spec_path, data_path)
        - Loads and parses spec JSON and data JSON (reuses DashRenderer._load_data logic)
        - Stores spec dict, raw DataFrame, variable labels, value labels

    build(output_path, port=5006)
        - Generates a complete, executable Bokeh Server app .py file
        - Writes the file to output_path
        - Returns nothing

    _embed_data()
        - base64-encodes spec JSON and data JSON as UTF-8 strings
        - Returns (spec_b64, data_b64) tuple
        - Base64 encoding prevents any special character in data from breaking
          the generated Python string literals

    _generate_app_source(port)
        - Returns the full Python source string for the server app
        - Structure: imports → embedded data constants → helper functions →
          make_document(doc) → __main__ block
```

**Generated app file structure:**
```python
# Auto-generated by dash — do not edit
import base64, html, json, math
import numpy as np
import pandas as pd
from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler
from bokeh.models import (ColumnDataSource, Select, Slider, RangeSlider,
                           Div, HoverTool, BoxSelectTool, LassoSelectTool,
                           PanTool, WheelZoomTool, ResetTool)
from bokeh.plotting import figure
from bokeh.layouts import column, row, gridplot

_SPEC_B64 = "<base64_spec_string>"
_DATA_B64 = "<base64_data_string>"

def _load_spec_and_data():
    # decode, parse, return (spec_dict, DataFrame, meta_dict)

def _compute_histogram(df, varname, bins=20):
    # returns dict(top=[], left=[], right=[])

def _compute_lfit(df, yvar, xvar):
    # returns dict(x=[], y=[])

def _compute_qfit(df, yvar, xvar):
    # returns dict(x=[], y=[])

def _compute_kdensity(df, varname):
    # returns dict(x=[], y=[])

def _compute_lowess(df, yvar, xvar):
    # returns dict(x=[], y=[])

def _compute_kpi(df, stat, varname):
    # implements mean/sum/count/dcount/min/max/median/sd/p25/p50/p75
    # returns float

def _format_kpi(value, fmt_str):
    # Python-side numeric formatting (mimics Stata fmt)

def make_document(doc):
    spec, df, meta = _load_spec_and_data()
    # Build one ColumnDataSource per linked group (raw data)
    # Build separate ColumnDataSource per aggregated plot layer
    # Build figures using GlyphMapper-equivalent logic
    # Build KPI Divs
    # Build filter widgets with Python on_change callbacks
    # Python filter callback:
    #   1. Recompute mask from all active widgets
    #   2. Replace raw sources' .data with filtered dict
    #   3. Replace aggregate sources' .data (histogram, lfit, etc.)
    #   4. Recompute and update KPI Div.text
    # Brush callback on source.selected:
    #   Recompute brush-mode KPIs from selected indices
    # Assemble layout with gridplot + filter bar
    doc.add_root(layout)
    doc.title = "<escaped title>"

if __name__ == '__main__':
    server = Server(
        {'/': Application(FunctionHandler(make_document))},
        port=<PORT>,
        allow_websocket_origin=['localhost:<PORT>']
    )
    server.start()
    server.io_loop.add_callback(server.show, '/')
    print('Bokeh Server running at http://localhost:<PORT>/')
    print('Press Ctrl+C to stop.')
    try:
        server.io_loop.start()
    except KeyboardInterrupt:
        pass
    finally:
        server.stop()
```

**Security:** All user strings (title, KPI labels, variable names embedded in Div.text) are
passed through `html.escape()` before being embedded in the generated Python string.
The data payload is base64-encoded to prevent injection via data values.

#### TR-8: Tests — `test/test_server.py`

Python pytest file covering:
- `ServerAppBuilder.build()` produces syntactically valid Python (`compile()` or `ast.parse()`)
- Generated file contains `make_document` and `__main__` block
- `make_document` is importable and callable — returns without error on mock `Document`
- Histogram ColumnDataSource updates when filter callback fires with filtered data
- lfit ColumnDataSource updates slope when filter callback fires
- KPI Div text updates correctly when filter fires and when brush selection changes
- `allow_websocket_origin` present in generated `__main__` block
- `--mode standalone` still produces HTML (regression test)
- HTML-escaped titles do not appear unescaped in generated file
- base64-encoded data round-trips correctly

#### TR-9: Certification Script — `test/test_e2e_serve.cscript`

Stata cscript covering:
- Python availability check (same `capture { python: pass end }` pattern)
- `dash serve` with empty registry → error 198 with descriptive message
- `dash serve, port(99999)` → error 198
- `dash serve, port(abc)` → error 198
- `dash build, saving(t.py) server` → `.py` file created
- Generated `.py` file is syntactically valid Python (verified via `python: import ast`)
- Generated `.py` file contains `make_document` string
- Generated `.py` file contains `Server` string
- `make_document` can be called on a Bokeh Document without error

---

### 4.4 Data Flow — Server Mode

```
dash scatter mpg weight, name(s1)
dash kpi mean(mpg), title("Avg MPG") name(k1) update(both)
dash serve [, port(5006)]
    → dash.ado:
        1. Serialize variables via jsonio → temp data.json
        2. Assemble master JSON with "mode":"server"
        3. python: dash_render.py --mode server → writes temp _app.py
        4. python: load make_document from _app.py
                   Server({'/': make_document}, port=5006).start()
                   io_loop.start()   ← BLOCKS until Ctrl+C
    → Browser opens at http://localhost:5006/
    → User interacts:
        [select dropdown "Foreign"]
          → Python callback: mask = df['foreign']==1
          → scatter source.data = df[mask]
          → KPI Div.text = f"Avg MPG: {df[mask]['mpg'].mean():.1f}"
        [brush selection in scatter]
          → Python callback: indices = source.selected.indices
          → KPI (update=both): recomputes mean from df.iloc[indices]
    → User presses Ctrl+C
    → server.stop(); Stata returns to prompt
```

---

### 4.5 Comparison: Standalone vs Server Mode

| Capability | Standalone HTML | Server Mode |
|---|---|---|
| Deployment | Single .html file — share or open anywhere | Requires Python + Bokeh installed; run `bokeh serve app.py` or `dash serve` |
| KPI on filter | Pre-computed (all combinations at build) | Recomputed dynamically from filtered DataFrame |
| KPI on brush | Not supported | Fully supported via `selected.on_change` |
| Histogram recompute | Not supported | Bins recomputed via numpy.histogram on filtered data |
| lfit/qfit recompute | Not supported | Coefficients recomputed via numpy.polyfit on filtered data |
| kdensity recompute | Not supported | KDE recomputed via scipy.stats.gaussian_kde |
| All plot types in brush | Raw glyphs only | All plot types (aggregated sources replace their own .data) |
| Dataset size limit | ~200K rows (embedded in HTML) | Unlimited (data stays in Python process) |
| Multi-user | N/A (each user has own file) | Each browser connection gets own document instance |

---

### 4.6 Test Plan — Phase 4

| File | Coverage |
|---|---|
| `test/test_server.py` | ServerAppBuilder correctness; callback behavior; security |
| `test/test_e2e_serve.cscript` | Stata-side subcommand routing, validation, app file generation |

### Adversarial Tests for `dash serve`

| Attack | Vector | Expected |
|---|---|---|
| Port injection | `port("5006; drop_tables()")` | Rejected by regex; not an integer |
| XSS in server mode | `title("<script>alert(1)</script>")` | html.escape() in generated Div.text |
| Data payload injection | Data column containing `\'` + `\n` | Base64 encoding prevents any escape |
| WebSocket hijack | Cross-origin request | `allow_websocket_origin` restricts to localhost |
| Resource exhaustion | 1000 browser tabs to server | `num_procs=1` + Tornado's built-in connection limits |
