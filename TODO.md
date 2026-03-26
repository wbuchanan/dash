# TODO: dash — Multi-Graph Interactive Dashboards from Stata twoway Syntax

Items are ordered so that dependencies always appear before dependents.
Status: [ ] not started | [~] in progress | [x] complete

---

## SETUP & INFRASTRUCTURE

- [x] S-01  Create repo directory structure: test/, examples/ subdirectories
- [x] S-02  Write dash_setup.ado: check Python availability via `python query`
- [x] S-03  dash_setup.ado: install/verify bokeh, numpy, scipy, statsmodels, pandas via pip
- [x] S-04  dash_setup.ado: check for jsonio via `which jsonio`; auto-install via `ssc install jsonio` if missing
- [x] S-05  dash_setup.ado: report installation status for each dependency
- [x] S-06  dash_setup.ado: verify minimum package versions (bokeh>=3.0, numpy>=1.23, scipy>=1.9, statsmodels>=0.13, pandas>=1.5)
- [x] S-07  Write dash_setup.sthlp: SMCL help file for setup command
- [x] S-08  Write dash_render.py: full implementation of DashRenderer, GlyphMapper, OptionTranslator, FilterBuilder

---

## PHASE 1A — CORE INFRASTRUCTURE

### Mata Parser

- [x] P1A-01  Write dash_parse.mata: define token type constants (OPEN_PAREN, CLOSE_PAREN, WORD, COMMA, PIPE_PIPE, QUOTED_STRING)
- [x] P1A-02  dash_parse.mata: implement Pass 1 tokenizer — character-by-character scan with paren depth tracking
- [x] P1A-03  dash_parse.mata: handle double-quoted strings ("...") in tokenizer — preserve contents, no depth tracking inside
- [x] P1A-04  dash_parse.mata: handle compound quoted strings (`"..."') in tokenizer
- [x] P1A-05  dash_parse.mata: detect || separator as PIPE_PIPE token
- [x] P1A-06  dash_parse.mata: detect comma at depth 0 as scope delimiter vs comma inside option parens
- [x] P1A-07  dash_parse.mata: implement Pass 2 structural parser — group tokens into plot specs (parenthetical and || forms)
- [x] P1A-08  dash_parse.mata: extract plot type (first word), varlist (subsequent words before comma), and options (after comma) from each plot spec
- [x] P1A-09  dash_parse.mata: extract graph-level options (all tokens after final top-level comma)
- [x] P1A-10  dash_parse.mata: build abbreviation lookup table — marker options: mc→mcolor, ms→msymbol, msi→msize, mla→mlabel, mlc→mlabcolor, mls→mlabsize
- [x] P1A-11  dash_parse.mata: build abbreviation lookup table — line options: lc→lcolor, lw→lwidth, lp→lpattern
- [x] P1A-12  dash_parse.mata: build abbreviation lookup table — graph options: ti→title, sub→subtitle, xti→xtitle, yti→ytitle, xla→xlabel, yla→ylabel, note→note, cap→caption
- [x] P1A-13  dash_parse.mata: implement abbreviation expansion — apply table to all extracted option names
- [x] P1A-14  dash_parse.mata: validate plot type against supported list; emit error for unsupported types
- [x] P1A-15  dash_parse.mata: validate variable names exist in dataset (`confirm variable`)
- [x] P1A-16  dash_parse.mata: detect and reject non-UTF-8 bytes in input string
- [x] P1A-17  dash_parse.mata: output structured JSON string per graph spec
- [x] P1A-18  dash_parse.mata: handle `if` qualifier — extract condition string and include in JSON
- [x] P1A-19  dash_parse.mata: handle `in` qualifier — extract range and include in JSON

### Certification Scripts — Tokenizer

- [x] P1A-20  test/test_tokenizer.cscript: test single word tokenizes to single WORD token
- [x] P1A-21  test/test_tokenizer.cscript: test double-quoted string preserves contents as QUOTED_STRING
- [x] P1A-22  test/test_tokenizer.cscript: test compound-quoted string (`"..."') tokenizes correctly
- [x] P1A-23  test/test_tokenizer.cscript: test parenthesis depth tracking — nested option parens don't split incorrectly
- [x] P1A-24  test/test_tokenizer.cscript: test comma at depth 0 produces COMMA token
- [x] P1A-25  test/test_tokenizer.cscript: test comma inside option parens does NOT produce scope-delimiter COMMA
- [x] P1A-26  test/test_tokenizer.cscript: test || produces PIPE_PIPE token
- [x] P1A-27  test/test_tokenizer.cscript: test empty input returns empty token array without error
- [x] P1A-28  test/test_tokenizer.cscript: test 1000-character input (resource exhaustion boundary)
- [x] P1A-29  test/test_tokenizer.cscript: test unicode characters in quoted strings pass through correctly
- [x] P1A-30  test/test_tokenizer.cscript: test unbalanced parentheses produces appropriate error

### Certification Scripts — Parser

- [x] P1A-31  test/test_parser.cscript: parse `scatter y x` → single plot spec, correct yvar/xvar
- [x] P1A-32  test/test_parser.cscript: parse `scatter y x, mc(red) msi(large)` → options dict with mcolor/msize expanded
- [x] P1A-33  test/test_parser.cscript: parse `(scatter y x) (lfit y x)` → two plot specs
- [x] P1A-34  test/test_parser.cscript: parse `(scatter y x, mc(red)) (lfit y x, lc(blue)), title("T")` → plot-level and graph-level options correct
- [x] P1A-35  test/test_parser.cscript: parse `scatter y x || lfit y x` (|| syntax) → two plot specs
- [x] P1A-36  test/test_parser.cscript: test abbreviation expansion: sc→scatter, tw→twoway, mc→mcolor, ms→msymbol
- [x] P1A-37  test/test_parser.cscript: test `name()` option extracted into graph_options
- [x] P1A-38  test/test_parser.cscript: test `if foreign == 1` qualifier extracted into JSON
- [x] P1A-39  test/test_parser.cscript: test `in 1/50` qualifier extracted into JSON
- [x] P1A-40  test/test_parser.cscript: test invalid plot type (e.g., "foobar") produces error 198
- [x] P1A-41  test/test_parser.cscript: test missing variable name produces confirm error
- [x] P1A-42  test/test_parser.cscript: test option value containing `); import os` treated as literal string (injection)
- [x] P1A-43  test/test_parser.cscript: test title containing `<script>alert(1)</script>` present in JSON as escaped HTML

### dash.ado — Single-Graph Mode

- [x] P1A-44  dash.ado: capture full command string via `0'
- [x] P1A-45  dash.ado: detect subcommand type — plot definition (default), `kpi`, `build`, `clear`
- [x] P1A-46  dash.ado: for plot definition without `name()` — immediate single-graph render path
- [x] P1A-47  dash.ado: extract `saving()` option; validate path (no `..`, `.html` suffix, writeable)
- [x] P1A-48  dash.ado: call dash_parse.mata on plot spec string; retrieve JSON via local macro
- [x] P1A-49  dash.ado: determine variables needed from parsed JSON
- [x] P1A-50  dash.ado: call jsonio to serialize needed variables → temp JSON file
- [x] P1A-51  dash.ado: pass spec JSON path + data JSON path to Python via `python:` block
- [x] P1A-52  dash.ado: Python block calls DashRenderer; writes HTML to saving() path
- [x] P1A-53  dash.ado: open HTML in default browser if no `saving()` or if `browse` option specified
- [x] P1A-54  dash.ado: validate all string option values are valid UTF-8 before passing to Python
- [x] P1A-55  dash.ado: HTML-escape all user-supplied string values before embedding in output

### Python Renderer — Phase 1A

- [x] P1A-56  dash_render.py: DashRenderer.__init__ — load master spec JSON + jsonio data JSON
- [x] P1A-57  dash_render.py: DashRenderer._load_data — parse StataJSON envelope → pandas DataFrame; extract variableLabels, valueLabels, valueLabelNames, variableTypeIsString
- [x] P1A-58  dash_render.py: DashRenderer._load_data — build ColumnDataSource from DataFrame values
- [x] P1A-59  dash_render.py: DashRenderer._build_figures — for each graph spec, create Bokeh Figure with correct axis labels from variableLabels
- [x] P1A-60  dash_render.py: DashRenderer.render — assemble single figure and return file_html() output
- [x] P1A-61  dash_render.py: OptionTranslator.translate_mcolor — map Stata named colors (red, blue, green, navy, maroon, forest_green, etc.) to hex codes
- [x] P1A-62  dash_render.py: OptionTranslator.translate_mcolor — map RGB syntax `"255 0 0"` to hex
- [x] P1A-63  dash_render.py: OptionTranslator.translate_msymbol — map Stata marker names (circle, square, triangle, diamond, plus, x, etc.) to Bokeh marker strings
- [x] P1A-64  dash_render.py: OptionTranslator.translate_msize — map keywords (tiny, vsmall, small, medsmall, medium, medlarge, large, vlarge, huge) to pixel sizes
- [x] P1A-65  dash_render.py: OptionTranslator.translate_lcolor — same color mapping as mcolor
- [x] P1A-66  dash_render.py: OptionTranslator.translate_lwidth — map keywords (vvthin, vthin, thin, medthin, medium, medthick, thick, vthick, vvthick) to pixel widths
- [x] P1A-67  dash_render.py: OptionTranslator.translate_lpattern — map Stata patterns (solid, dash, dot, dash_dot, shortdash, etc.) to Bokeh dash lists
- [x] P1A-68  dash_render.py: GlyphMapper.map_scatter — scatter() glyph with mcolor, msymbol, msize, mlabel options; hover tooltip with variable values
- [x] P1A-69  dash_render.py: GlyphMapper.map_line — line() glyph with lcolor, lwidth, lpattern; sort by x before rendering; hover tooltip
- [x] P1A-70  dash_render.py: GlyphMapper.map_connected — line() + scatter() glyphs combined; sorted by x
- [x] P1A-71  dash_render.py: GlyphMapper.map_area — varea() glyph with baseline at 0; fill color + alpha options
- [x] P1A-72  dash_render.py: GlyphMapper.map_bar — vbar() glyph; compute width from data range
- [x] P1A-73  dash_render.py: GlyphMapper.map_spike — segment() glyph from y=0 to y=value at each x
- [x] P1A-74  dash_render.py: all GlyphMapper methods — exclude Stata missing values (NaN) from ColumnDataSource before rendering
- [x] P1A-75  dash_render.py: apply graph-level options: title → Bokeh Title, xtitle/ytitle → axis_label, xlabel/ylabel → axis tick labels
- [x] P1A-76  dash_render.py: apply xscale(log)/yscale(log) → x_axis_type/y_axis_type="log"
- [x] P1A-77  dash_render.py: apply xline()/yline() → Bokeh Span annotations
- [x] P1A-78  dash_render.py: add BoxSelectTool, LassoSelectTool, WheelZoomTool, PanTool, ResetTool to all figures
- [x] P1A-79  dash_render.py: output standalone HTML via bokeh.io.save() or file_html()
- [x] P1A-80  dash_render.py: add Content-Security-Policy meta tag to output HTML restricting external scripts

### Python Unit Tests — Phase 1A

- [x] P1A-81  test/test_options.py: every Stata named color maps to a valid hex code (100+ color names)
- [x] P1A-82  test/test_options.py: RGB string `"255 0 0"` maps to `#ff0000`
- [x] P1A-83  test/test_options.py: every Stata marker symbol maps to a valid Bokeh marker string
- [x] P1A-84  test/test_options.py: all size keywords map to increasing pixel values
- [x] P1A-85  test/test_options.py: all line width keywords map to increasing pixel widths
- [x] P1A-86  test/test_options.py: all line pattern keywords map to valid Bokeh dash lists
- [x] P1A-87  test/test_options.py: invalid color name raises ValueError with clear message
- [x] P1A-88  test/test_glyphs.py: scatter glyph uses correct ColumnDataSource columns
- [x] P1A-89  test/test_glyphs.py: line glyph data is sorted by x variable
- [x] P1A-90  test/test_glyphs.py: connected glyph produces both line and scatter renderers
- [x] P1A-91  test/test_glyphs.py: area glyph produces varea renderer with baseline at 0
- [x] P1A-92  test/test_glyphs.py: bar glyph produces vbar renderer
- [x] P1A-93  test/test_glyphs.py: spike glyph produces segment renderer from y=0
- [x] P1A-94  test/test_glyphs.py: NaN values are excluded from all glyph data
- [x] P1A-95  test/test_glyphs.py: mcolor/msymbol/msize options applied to scatter glyph properties
- [x] P1A-96  test/test_glyphs.py: lcolor/lwidth/lpattern options applied to line glyph properties

---

## PHASE 1B — MULTI-GRAPH & LINKING

### dash.ado — Registry and Named Graphs

- [x] P1B-01  dash.ado: implement `name()` option parsing — extract identifier and optional `replace` sub-option
- [x] P1B-02  dash.ado: validate name identifier against regex `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$`
- [x] P1B-03  dash.ado: store raw plot spec in `$dash_spec_<name>` global macro
- [x] P1B-04  dash.ado: store graph-level options in `$dash_opts_<name>` global macro
- [x] P1B-05  dash.ado: append name to `$dash_graph_registry`; respect `replace` sub-option
- [x] P1B-06  dash.ado: error if name already exists without `replace` sub-option
- [x] P1B-07  dash.ado: implement `dash clear` subcommand — drop all `$dash_*` globals

### dash.ado — Build Subcommand

- [x] P1B-08  dash.ado: implement `dash build` subcommand entry point
- [x] P1B-09  dash.ado: parse `dash build` options: saving(), title(), subtitle(), layout(), link(), filter(), theme(), replace
- [x] P1B-10  dash.ado: validate saving() path (no `..`, `.html` extension, confirm new/existing file)
- [x] P1B-11  dash.ado: validate all names in link() exist in $dash_graph_registry
- [x] P1B-12  dash.ado: validate all names in filter(... exclude()) exist in $dash_graph_registry
- [x] P1B-13  dash.ado: validate layout() argument — `rows cols` integers or `auto`
- [x] P1B-14  dash.ado: for each registered name, pass $dash_spec_<name> to dash_parse.mata; collect per-graph JSON
- [x] P1B-15  dash.ado: determine union of all variables needed across all specs
- [x] P1B-16  dash.ado: call jsonio to serialize all needed variables to temp JSON file
- [x] P1B-17  dash.ado: assemble master JSON: array of per-graph specs + build options (layout, link, filter list, theme)
- [x] P1B-18  dash.ado: write master JSON to temp file; pass both JSON paths to Python renderer
- [x] P1B-19  dash.ado: Python block calls DashRenderer; writes HTML to saving() path; opens browser

### dash_render.py — Multi-Graph Layout

- [x] P1B-20  dash_render.py: DashRenderer._build_figures — build one Bokeh Figure per registered graph; apply all graph-level options
- [x] P1B-21  dash_render.py: parse layout(rows cols) → target grid dimensions
- [x] P1B-22  dash_render.py: parse layout(auto) → compute grid dimensions from graph count (prefer square-ish)
- [x] P1B-23  dash_render.py: assemble figures into Bokeh gridplot() with specified rows/cols; leave empty cells for under-populated grids
- [x] P1B-24  dash_render.py: parse explicit placement syntax `layout(s1:1,1 s2:1,2)` → position each named graph
- [x] P1B-25  dash_render.py: apply sizing_mode="stretch_width" to all figures and gridplot for responsive layout

### dash_render.py — Linked Brushing

- [x] P1B-26  dash_render.py: DashRenderer._setup_linking — parse link() list from build options
- [x] P1B-27  dash_render.py: for graphs in link group — create ONE shared ColumnDataSource from their union of variables
- [x] P1B-28  dash_render.py: for graphs NOT in link group — create independent ColumnDataSource per figure
- [x] P1B-29  dash_render.py: set nonselection_glyph alpha=0.15 on all glyph renderers in linked figures
- [x] P1B-30  dash_render.py: handle link(_all) — all registered graphs share one ColumnDataSource

### Python Unit Tests — Phase 1B

- [x] P1B-31  test/test_layout.py: layout(2 2) with 4 graphs → 2x2 gridplot
- [x] P1B-32  test/test_layout.py: layout(auto) with 3 graphs → reasonable auto grid (e.g., 2x2 with 1 empty)
- [x] P1B-33  test/test_layout.py: layout(auto) with 1 graph → 1x1 grid
- [x] P1B-34  test/test_layout.py: fewer graphs than grid cells → empty cells (None) in gridplot
- [x] P1B-35  test/test_layout.py: sizing_mode="stretch_width" applied to all figures
- [x] P1B-36  test/test_linking.py: graphs in link() share exact same ColumnDataSource object reference
- [x] P1B-37  test/test_linking.py: graphs NOT in link() have distinct ColumnDataSource objects
- [x] P1B-38  test/test_linking.py: link(_all) → all figures share one ColumnDataSource
- [x] P1B-39  test/test_linking.py: nonselection_alpha=0.15 on renderers in linked figures
- [x] P1B-40  test/test_linking.py: attempting a second link() group raises error (single group enforced)

### Additional Plot Types — Phase 1B

- [x] P1B-41  dash_render.py: GlyphMapper.map_lfit — compute OLS coefficients via numpy.polyfit(x,y,1); render line() over x range
- [x] P1B-42  dash_render.py: GlyphMapper.map_qfit — compute quadratic fit via numpy.polyfit(x,y,2); render line() over x range
- [x] P1B-43  dash_render.py: GlyphMapper.map_lfitci — OLS fit + 95% CI band via scipy.stats; render line() + varea()
- [x] P1B-44  dash_render.py: GlyphMapper.map_qfitci — quadratic fit + CI band; render line() + varea()
- [x] P1B-45  dash_render.py: GlyphMapper.map_lowess — compute via statsmodels.nonparametric.lowess; render line()
- [x] P1B-46  dash_render.py: GlyphMapper.map_histogram — compute bins via numpy.histogram(); render quad() with bin edges; support bin() option
- [x] P1B-47  dash_render.py: GlyphMapper.map_kdensity — compute via scipy.stats.gaussian_kde; render line() of density curve
- [x] P1B-48  dash_parse.mata: add lfit, qfit, lfitci, qfitci, lowess, histogram, kdensity to supported plot type list
- [x] P1B-49  test/test_glyphs.py: lfit line passes through correct OLS fit (verify slope/intercept for known data)
- [x] P1B-50  test/test_glyphs.py: qfit line has 3 coefficients
- [x] P1B-51  test/test_glyphs.py: lfitci produces both line renderer and varea renderer
- [x] P1B-52  test/test_glyphs.py: histogram produces quad renderer with correct number of bins
- [x] P1B-53  test/test_glyphs.py: kdensity integrates to approximately 1.0 over its x range

### Legend Option

- [x] P1B-54  dash_render.py: apply legend() option — show/hide; set position (top_left, top_right, etc.); set label overrides from legend() string list
- [x] P1B-55  dash_render.py: use variableLabels as default legend labels when no explicit legend() labels provided
- [x] P1B-56  dash_render.py: use valueLabels for categorical legend entries when applicable

### if/in Qualification

- [x] P1B-57  dash.ado: extract `if` expression and pass to jsonio as `if` qualifier when calling jsonio out
- [x] P1B-58  dash.ado: extract `in` range and pass to jsonio as `in` qualifier
- [x] P1B-59  test/test_jsonio.cscript: load auto.dta; `jsonio out if foreign==1` → JSON has only matching records (verify count)
- [x] P1B-60  test/test_jsonio.cscript: `jsonio out in 1/10` → JSON has exactly 10 records

### jsonio Integration Tests

- [x] P1B-61  test/test_jsonio.cscript: load auto.dta; run jsonio out with what(all) metaprint(varnames varlabels vallabs labelnames); verify JSON contains variableNames array
- [x] P1B-62  test/test_jsonio.cscript: verify variableLabels object present with at least one label (mpg → "Mileage (mpg)")
- [x] P1B-63  test/test_jsonio.cscript: verify valueLabels object present (foreign → Domestic/Foreign)
- [x] P1B-64  test/test_jsonio.cscript: verify values array length matches observation count
- [x] P1B-65  test/test_jsonio.cscript: verify Stata missing values (.) handled — not present as nulls or errors in JSON

### Multi-Graph Certification Scripts

- [x] P1B-66  test/test_parser.cscript: parse named graph spec — verify name extracted into graph_options.name
- [x] P1B-67  test/test_e2e_multi.cscript: load auto.dta; define 3 named graphs; `dash build, saving(t.html) layout(2 2)`; verify HTML file exists and is non-empty
- [x] P1B-68  test/test_e2e_multi.cscript: verify output HTML contains all 3 graph name identifiers as DOM ids or Bokeh model ids
- [x] P1B-69  test/test_e2e_multi.cscript: verify output HTML contains Bokeh gridplot structure

---

## PHASE 1C — BY-GROUPS & POLISH

- [x] P1C-01  dash_parse.mata: extract `by(varname)` option from graph-level options
- [x] P1C-02  dash.ado: when by() present — enumerate distinct values of by-variable; create one sub-spec per value
- [x] P1C-03  dash_render.py: apply `if` condition per by-group value; render each group as separate figure
- [x] P1C-04  dash_render.py: assemble by-group figures into gridplot (small multiples); add group label as each figure title
- [x] P1C-05  dash_render.py: use valueLabels for by-group subplot titles when value labels exist
- [x] P1C-06  test/test_glyphs.py: by(foreign) on auto.dta → 2 figures produced (Domestic, Foreign)
- [x] P1C-07  dash.sthlp: write initial SMCL help file covering Phase 1A–1C features
- [x] P1C-08  dash.sthlp: {vieweralsosee} redirects for twoway and all Phase 1 supported plot types
- [x] P1C-09  dash.sthlp: Syntax section — all 4 command forms (single, named, kpi, build)
- [x] P1C-10  dash.sthlp: "Differences from twoway" section — interactive output; name() repurposed; new subcommands; unsupported options with Phase timelines
- [x] P1C-11  dash.sthlp: Dashboard Options synoptset for dash build (layout, link, theme, saving)
- [x] P1C-12  dash.sthlp: Plot options cross-reference table pointing to existing Stata help pages
- [x] P1C-13  dash.sthlp: Examples section — basic scatter through multi-graph layout
- [x] P1C-14  dash.sthlp: Dependencies section — dash_setup usage
- [x] P1C-15  test/test_e2e_single.cscript: load auto.dta; `dash scatter mpg weight, saving(t.html)`; assert file exists; assert HTML contains Bokeh embed string
- [x] P1C-16  test/test_e2e_single.cscript: load auto.dta; `dash (scatter mpg weight) (lfit mpg weight), saving(t.html)`; assert HTML contains lfit data
- [x] P1C-17  test/test_e2e_single.cscript: assert variable label "Mileage (mpg)" appears in output HTML as axis title
- [x] P1C-18  test/test_e2e_single.cscript: assert value labels "Domestic"/"Foreign" appear in output HTML
- [x] P1C-19  examples/basic_scatter.do: working example script — single scatter plot
- [x] P1C-20  examples/multi_graph_dashboard.do: working example — 3-graph dashboard with layout

---

## PHASE 2 — FILTERS, KPIs, ADVANCED INTERACTION

### dash.ado — KPI Subcommand

- [x] P2-01  dash.ado: implement `dash kpi` subcommand parsing — extract statistic(varname), title(), name(), fmt(), subtitle(), color(), bgcolor(), update()
- [x] P2-02  dash.ado: validate statistic is one of: mean, sum, count, dcount, min, max, median, sd, p25, p50, p75
- [x] P2-03  dash.ado: compute mean/sum/min/max/sd via `summarize`; store r(mean)/r(sum)/r(min)/r(max)/r(sd)
- [x] P2-04  dash.ado: compute count via `summarize`; store r(N)
- [x] P2-05  dash.ado: compute dcount (distinct count) via `codebook varname`; parse unique value count from output
- [x] P2-06  dash.ado: compute median/p25/p75 via `_pctile varname, p(25 50 75)`; store r(r1)/r(r2)/r(r3)
- [x] P2-07  dash.ado: apply `if`/`in` qualifiers before computing KPI value
- [x] P2-08  dash.ado: format computed value using fmt() Stata format string; store formatted string
- [x] P2-09  dash.ado: validate update() is one of: filter, brush, both; default to filter
- [x] P2-10  dash.ado: store KPI definition in `$dash_kpi_<name>` as semicolon-delimited field string
- [x] P2-11  dash.ado: append KPI name to `$dash_graph_registry` so it participates in layout

### dash_render.py — KPI Cards

- [x] P2-12  dash_render.py: DashRenderer._build_kpis — for each KPI entry, create Bokeh Div with styled HTML (title, large value, subtitle)
- [x] P2-13  dash_render.py: KPI Div HTML template — background color, border-radius, padding, large font for value, smaller for title/subtitle
- [x] P2-14  dash_render.py: color and bgcolor options override default KPI card styling
- [x] P2-15  dash_render.py: KPI with update(filter) — attach CustomJS to each filter widget's `value` property change; JS recomputes aggregate from filtered source data and updates Div.text
- [x] P2-16  dash_render.py: KPI with update(brush) — attach CustomJS to source.selected.indices change; JS recomputes aggregate from selected rows and updates Div.text
- [x] P2-17  dash_render.py: KPI with update(both) — attach both filter and brush listeners
- [x] P2-18  dash_render.py: CustomJS for KPI recomputation — implement mean, sum, count, min, max aggregations in JavaScript against filtered/selected data arrays
- [x] P2-19  dash_render.py: CustomJS for KPI — implement dcount (distinct count) in JavaScript using Set()
- [x] P2-20  dash_render.py: CustomJS for KPI — implement median, p25, p75 in JavaScript (sort + index)
- [x] P2-21  dash_render.py: CustomJS for KPI — apply Stata format string to computed JS value (numeric formatting)
- [x] P2-22  dash_render.py: place KPI Div widgets in gridplot layout alongside graph figures

### dash_render.py — Filters

- [x] P2-23  dash_render.py: FilterBuilder.build_dropdown — create Bokeh Select widget; options from sorted unique values; use valueLabels if available; "All" option prepended
- [x] P2-24  dash_render.py: FilterBuilder.build_dropdown — CustomJS callback applies BooleanFilter to CDSView of each non-excluded graph's renderers; calls source.change.emit()
- [x] P2-25  dash_render.py: FilterBuilder.build_slider — create Bokeh Slider widget; min/max from data range; step auto-computed
- [x] P2-26  dash_render.py: FilterBuilder.build_slider — CustomJS filters CDSView rows where var >= slider.value
- [x] P2-27  dash_render.py: FilterBuilder.build_range — create Bokeh RangeSlider widget; min/max from data range
- [x] P2-28  dash_render.py: FilterBuilder.build_range — CustomJS filters CDSView rows where var >= start AND var <= end
- [x] P2-29  dash_render.py: all filter CustomJS — HTML-escape all user-provided variable names and values before interpolation into JS templates
- [x] P2-30  dash_render.py: all filter CustomJS — parameterized templates (no direct string interpolation of user values into JS code paths)
- [x] P2-31  dash_render.py: parse exclude() sub-option — pass list of excluded names to FilterBuilder; skip those figures/KPIs in callbacks
- [x] P2-32  dash_render.py: place filter widgets in a row above the main gridplot layout

### Python Unit Tests — Phase 2

- [x] P2-33  test/test_kpi.py: mean(mpg) on auto.dta fixture → correct float value
- [x] P2-34  test/test_kpi.py: sum(price) on auto.dta fixture → correct sum
- [x] P2-35  test/test_kpi.py: count(mpg) → correct integer (74 for auto.dta)
- [x] P2-36  test/test_kpi.py: dcount(rep78) → correct distinct count (5)
- [x] P2-37  test/test_kpi.py: min(price), max(price) → correct values
- [x] P2-38  test/test_kpi.py: median(mpg) → correct value
- [x] P2-39  test/test_kpi.py: p25(mpg), p75(mpg) → correct quartile values
- [x] P2-40  test/test_kpi.py: sd(mpg) → correct standard deviation
- [x] P2-41  test/test_kpi.py: fmt(%9.1f) applied to mean → string with 1 decimal place
- [x] P2-42  test/test_kpi.py: KPI Div HTML contains title text, formatted value, subtitle text
- [x] P2-43  test/test_kpi.py: update(filter) → CustomJS attached to widget value property, NOT to selected.indices
- [x] P2-44  test/test_kpi.py: update(brush) → CustomJS attached to selected.indices, NOT to widget value
- [x] P2-45  test/test_kpi.py: update(both) → CustomJS attached to both
- [x] P2-46  test/test_kpi.py: dcount JS implementation: Set([1,1,2,3]) has size 3
- [x] P2-47  test/test_kpi.py: median JS implementation: sorted [1,2,3,4,5] → 3.0
- [x] P2-48  test/test_filters.py: dropdown widget options list matches sorted unique values of variable
- [x] P2-49  test/test_filters.py: dropdown uses valueLabels for option display text when available
- [x] P2-50  test/test_filters.py: "All" option always present as first dropdown entry
- [x] P2-51  test/test_filters.py: dropdown CustomJS references correct CDSView for each non-excluded figure
- [x] P2-52  test/test_filters.py: excluded graphs (exclude(k1)) do NOT appear in dropdown CustomJS callback
- [x] P2-53  test/test_filters.py: slider widget min/max match data range
- [x] P2-54  test/test_filters.py: range slider min/max match data range
- [x] P2-55  test/test_filters.py: filter CustomJS contains no un-escaped user string interpolation

### Additional Plot Types — Phase 2

- [x] P2-56  dash_render.py: GlyphMapper.map_rarea — varea() with explicit y1/y2 columns
- [x] P2-57  dash_render.py: GlyphMapper.map_rbar — vbar() with bottom= and top= columns
- [x] P2-58  dash_render.py: GlyphMapper.map_rspike — segment() glyph from y1 to y2 at each x
- [x] P2-59  dash_render.py: GlyphMapper.map_rcap — segment() glyph + horizontal end caps via scatter() or segment()
- [x] P2-60  dash_render.py: GlyphMapper.map_rline — line() connecting (x, y1) and (x, y2) points
- [x] P2-61  dash_render.py: GlyphMapper.map_rconnected — line() + scatter() for range-connected variant
- [x] P2-62  dash_render.py: GlyphMapper.map_dot — scatter() with manipulated axis for dot plot layout
- [x] P2-63  dash_parse.mata: add rarea, rbar, rspike, rcap, rline, rconnected, dot to supported plot type list; update varlist parsing for 3-variable range plots (y1 y2 x)
- [x] P2-64  test/test_glyphs.py: rarea produces varea with upper/lower columns
- [x] P2-65  test/test_glyphs.py: rbar produces vbar with bottom/top columns
- [x] P2-66  test/test_glyphs.py: rcap produces segment renderer with end caps

### Dashboard Theme Option

- [x] P2-67  dash_render.py: implement theme() support — define color palettes, font sizes, background colors for named themes
- [x] P2-68  dash_render.py: theme(clean) — white background, minimal grid lines, clean typography
- [x] P2-69  dash_render.py: theme(dark) — dark background variant
- [x] P2-70  dash_render.py: apply theme properties to all figures and KPI card styles

### Performance

- [x] P2-71  dash_render.py: enable WebGL backend for figures when observation count > 10,000 (output_backend="webgl")
- [x] P2-72  dash_render.py: detect row count from ColumnDataSource; set webgl threshold conditionally

### Phase 2 E2E and Adversarial Certification Scripts

- [x] P2-73  test/test_e2e_filters.cscript: load auto.dta; define 2 graphs; `dash build, filter(foreign, type(dropdown))`; verify HTML contains Bokeh Select widget
- [x] P2-74  test/test_e2e_filters.cscript: verify "Domestic" and "Foreign" (value labels) appear in filter widget options in HTML
- [x] P2-75  test/test_e2e_filters.cscript: verify "All" option present in filter widget HTML
- [x] P2-76  test/test_e2e_kpi.cscript: load auto.dta; `dash kpi mean(mpg), title("Avg MPG") name(k1) fmt(%9.1f)`; `dash build, saving(t.html)`; verify HTML contains formatted mean value string
- [x] P2-77  test/test_e2e_kpi.cscript: verify KPI card HTML structure (title text, value, styled div) present in output
- [x] P2-78  test/test_adversarial.cscript: XSS — `title("<script>alert(1)</script>")` → verify `<script>` is HTML-escaped (`&lt;script&gt;`) in output HTML
- [x] P2-79  test/test_adversarial.cscript: shell injection — varname containing semicolons or backticks → verify Mata parser rejects or sanitizes
- [x] P2-80  test/test_adversarial.cscript: path traversal — `saving("../../../tmp/evil.html")` → verify error returned, no file written
- [x] P2-81  test/test_adversarial.cscript: Python injection — option value `"red); import os; os.system('id')"` → verify value treated as literal, no OS call
- [x] P2-82  test/test_adversarial.cscript: resource exhaustion — varlist with 200 variable names → verify graceful error (not crash or hang)
- [x] P2-83  test/test_adversarial.cscript: stack overflow — 100 levels of nested parentheses → verify graceful error
- [x] P2-84  test/test_adversarial.cscript: JS injection — filter variable name containing JS code → verify escaped in CustomJS template

### SMCL Help Updates — Phase 2

- [x] P2-85  dash.sthlp: add KPI Cards section — syntax, all supported statistics (incl. dcount), update() option, examples
- [x] P2-86  dash.sthlp: add Filters section — filter(), type(), exclude() sub-option, examples for dropdown/slider/range
- [x] P2-87  dash.sthlp: update Dashboard Options synoptset with filter(), link(), layout(), theme()
- [x] P2-88  dash.sthlp: add {vieweralsosee} for rarea, rbar, rspike, rcap, rline, rconnected, dot

---

## PHASE 3 — POLISH & DISTRIBUTION

### Scheme Translation

- [x] P3-01  dash_render.py: implement scheme(s2color) — apply Stata s2color palette and styling
- [x] P3-02  dash_render.py: implement scheme(plotplain) — apply plotplain minimal styling
- [x] P3-03  test/test_options.py: scheme(s2color) → Bokeh figures have s2color background and palette colors

### Export

- [x] P3-04  dash.ado: implement `dash export, format(png)` — call Bokeh export_png() on last-rendered figure
- [x] P3-05  dash.ado: implement `dash export, format(svg)` — call Bokeh export_svg()
- [x] P3-06  dash_setup.ado: check for selenium/webdriver (required for Bokeh PNG/SVG export); install if missing
- [x] P3-07  test/test_e2e_single.cscript: verify PNG export produces a valid PNG file (check file header bytes 0x89 0x50 0x4E 0x47)

### Error Messages

- [x] P3-08  dash.ado: every error condition has a descriptive message with suggested fix (no bare error codes alone)
- [x] P3-09  dash_render.py: every exception caught and re-raised with context (graph name, option, value that caused failure)
- [x] P3-10  dash_parse.mata: every parse error includes the offending token and position in string

### Performance Benchmarks

- [x] P3-11  examples/full_dashboard.do: benchmark script — generate 100K-row dataset; run full multi-graph dashboard; time the render
- [x] P3-12  Verify 100K rows renders in < 30 seconds on reference machine; document result in comments

### Security Audit

- [x] P3-13  Review all places user strings are embedded in Python code (via macro/sfi) — verify no eval/exec paths
- [x] P3-14  Review all CustomJS templates — verify parameterized construction; no raw user value interpolation into JS
- [x] P3-15  Review file path handling in dash.ado — verify no `..` traversal possible with any input
- [x] P3-16  Run all adversarial certification scripts against final codebase; verify all pass
- [x] P3-17  Verify no API keys or credentials anywhere in codebase (search for api_key, password, secret, token patterns)

### Packaging

- [x] P3-18  Create dash.pkg — package descriptor for SSC submission
- [x] P3-19  Create stata.toc — table of contents entry
- [x] P3-20  Verify all .ado, .mata, .py, .sthlp files listed in dash.pkg
- [x] P3-21  Test cold-install: fresh Stata session, run dash_setup, verify all dependencies install and basic scatter works

### Final Documentation

- [x] P3-22  dash.sthlp: complete all remaining sections with all Phase 2 options fully documented
- [x] P3-23  dash.sthlp: comprehensive Examples section — basic → multi-graph → KPIs + filters (reference examples/*.do)
- [x] P3-24  dash_setup.sthlp: document all dependencies, minimum versions, troubleshooting steps
- [x] P3-25  examples/full_dashboard.do: fully-commented working example with KPIs, multiple graphs, filters, linking

---

## CONTINUOUS REQUIREMENTS (apply throughout all phases)

- [x] C-01  Before every commit: run all .cscript tests via `do test/test_*.cscript` and verify no failures
- [x] C-02  Before every commit: run all Python tests via `pytest test/` and verify all pass
- [x] C-03  Before every commit: pull from main branch; resolve any conflicts before committing
- [x] C-04  All new Stata code (.ado, .mata): add block comment header (purpose, arguments, returns, author, version)
- [x] C-05  All new Python code: add Google-style docstrings to every class and method
- [x] C-06  All new Python code: inline comments on non-obvious logic (CustomJS generation, Bokeh model assembly)
- [x] C-07  Commit to feature branch; never directly to main
- [x] C-08  Commit messages: describe the change; no Claude/Anthropic references (CLAUDE.md rule 7)

---

## PHASE 4 — BOKEH SERVER / `dash serve`

### dash.ado — `serve` Subcommand Entry Point

- [x] P4-01  dash.ado: detect `serve` as first token of `$0`; route to `_dash_serve`
- [x] P4-02  dash.ado: implement `_dash_serve` program with `syntax [, PORT(string) NOBROWSER TIMEOUT(string)]`
- [x] P4-03  dash.ado: `_dash_serve` — validate port() is a positive integer using `regexm`; default to 5006
- [x] P4-04  dash.ado: `_dash_serve` — validate port() is in range 1024–65535; exit(198) with descriptive message if not
- [x] P4-05  dash.ado: `_dash_serve` — validate timeout() is non-negative integer; default to 0 (no timeout)
- [x] P4-06  dash.ado: `_dash_serve` — require `$dash_graph_registry` non-empty; exit(198) with descriptive message if empty
- [x] P4-07  dash.ado: `_dash_serve` — determine all required variables (identical logic to `_dash_build`)
- [x] P4-08  dash.ado: `_dash_serve` — serialize variables via jsonio to temp data.json (identical to `_dash_build`)
- [x] P4-09  dash.ado: `_dash_serve` — assemble master JSON including `"mode":"server"` in build_options
- [x] P4-10  dash.ado: `_dash_serve` — call `dash_render.py --mode server` via `python:` block; write temp `_app.py`
- [x] P4-11  dash.ado: `_dash_serve` — display server URL and stop instructions before blocking
- [x] P4-12  dash.ado: `_dash_serve` — launch Bokeh Server via second `python:` block using `bokeh.server.server.Server`
- [x] P4-13  dash.ado: `_dash_serve` — open browser at localhost:{port} unless `nobrowser` option specified
- [x] P4-14  dash.ado: `_dash_serve` — implement timeout via `tornado.ioloop.IOLoop.call_later()` when timeout() > 0
- [x] P4-15  dash.ado: `_dash_serve` — clean shutdown on KeyboardInterrupt; display "dash serve: Server stopped."

### dash.ado — `dash build, server` Option

- [x] P4-16  dash.ado: add `SERVER` to `_dash_build` syntax options
- [x] P4-17  dash.ado: when `server` option present, output path must end in `.py` not `.html`; validate accordingly
- [x] P4-18  dash.ado: when `server` option present, pass `--mode server` to `dash_render.py`; do NOT block; do NOT open browser
- [x] P4-19  dash.ado: after writing app file with `server` option, display `bokeh serve <file>` command for user

### dash_render.py — Argparse CLI Interface

- [x] P4-20  dash_render.py: replace positional-arg `__main__` block with `argparse` — required flags `--spec`, `--data`, `--output`
- [x] P4-21  dash_render.py: add optional `--mode` flag to argparse (values: `standalone`, `server`; default `standalone`)
- [x] P4-22  dash_render.py: update `main()` signature to `main(spec, data, output, mode='standalone')`
- [x] P4-23  dash_render.py: when `mode == 'standalone'` — existing `DashRenderer.render()` path unchanged
- [x] P4-24  dash_render.py: when `mode == 'server'` — instantiate `ServerAppBuilder` and call `build(output_path)`

### dash_render.py — `ServerAppBuilder` Class

- [x] P4-25  dash_render.py: define `ServerAppBuilder` class with `__init__(spec_path, data_path)`
- [x] P4-26  dash_render.py: `ServerAppBuilder.__init__` — load and parse spec JSON and data JSON using same logic as `DashRenderer._load_data()`
- [x] P4-27  dash_render.py: `ServerAppBuilder.build(output_path, port=5006)` — generate server app `.py` file and write to `output_path`
- [x] P4-28  dash_render.py: `ServerAppBuilder._embed_data()` — base64-encode spec JSON and data JSON; return (spec_b64, data_b64) tuple
- [x] P4-29  dash_render.py: `ServerAppBuilder._generate_app_source(port)` — return complete Python source string for server app
- [x] P4-30  dash_render.py: generated app — import block: base64, html, json, math, numpy, pandas, all required bokeh.models, bokeh.server.server.Server, Application, FunctionHandler
- [x] P4-31  dash_render.py: generated app — `_SPEC_B64` and `_DATA_B64` constants holding base64-encoded JSON
- [x] P4-32  dash_render.py: generated app — `_load_spec_and_data()` helper that decodes base64, parses JSON, builds DataFrame with correct dtypes, extracts variableLabels/valueLabels
- [x] P4-33  dash_render.py: generated app — `_compute_histogram(df, varname, bins=20)` helper returning dict(top, left, right)
- [x] P4-34  dash_render.py: generated app — `_compute_lfit(df, yvar, xvar)` helper returning dict(x, y) over data range with 100 points
- [x] P4-35  dash_render.py: generated app — `_compute_qfit(df, yvar, xvar)` helper for quadratic fit
- [x] P4-36  dash_render.py: generated app — `_compute_kdensity(df, varname)` helper using scipy.stats.gaussian_kde
- [x] P4-37  dash_render.py: generated app — `_compute_lowess(df, yvar, xvar)` helper using statsmodels
- [x] P4-38  dash_render.py: generated app — `_compute_kpi(df, stat, varname)` implementing all 11 supported statistics including dcount (using pd.Series.nunique)
- [x] P4-39  dash_render.py: generated app — `make_document(doc)` function as Bokeh Server document factory
- [x] P4-40  dash_render.py: generated app — `make_document`: call `_load_spec_and_data()` on each invocation (supports multi-user server)
- [x] P4-41  dash_render.py: generated app — `make_document`: build one shared ColumnDataSource per linked group for raw-data plots
- [x] P4-42  dash_render.py: generated app — `make_document`: build separate ColumnDataSource for each aggregated plot layer (histogram, lfit, qfit, kdensity, lowess)
- [x] P4-43  dash_render.py: generated app — `make_document`: build Bokeh figures, add glyphs using same plot type dispatch as GlyphMapper
- [x] P4-44  dash_render.py: generated app — `make_document`: build KPI Div widgets with styled HTML
- [x] P4-45  dash_render.py: generated app — `make_document`: build filter widgets (Select, Slider, RangeSlider) with Python `on_change` callbacks — NOT CustomJS
- [x] P4-46  dash_render.py: generated app — filter `on_change` callback: recompute boolean mask from all active widget values; replace raw source.data with filtered DataFrame dict
- [x] P4-47  dash_render.py: generated app — filter `on_change` callback: recompute each aggregate ColumnDataSource (histogram bins, lfit line, etc.) from filtered DataFrame and replace `.data`
- [x] P4-48  dash_render.py: generated app — filter `on_change` callback: recompute KPI values for all KPIs with `update in ('filter', 'both')`; update `Div.text`
- [x] P4-49  dash_render.py: generated app — brush callback via `source.selected.on_change('indices', cb)`: recompute KPIs for `update in ('brush', 'both')` from selected rows
- [x] P4-50  dash_render.py: generated app — assemble layout: filter bar row above gridplot (same structure as standalone)
- [x] P4-51  dash_render.py: generated app — `doc.add_root(layout)`; `doc.title` set to HTML-escaped dashboard title
- [x] P4-52  dash_render.py: generated app — `__main__` block: `Server({'/': Application(FunctionHandler(make_document))}, port=PORT, allow_websocket_origin=['localhost:PORT'])`
- [x] P4-53  dash_render.py: generated app — `__main__` block: `server.io_loop.add_callback(server.show, '/')`; graceful KeyboardInterrupt → `server.stop()`
- [x] P4-54  dash_render.py: security — HTML-escape all user strings (title, subtitle, KPI labels, variable names in Div.text) before embedding in generated Python string literals
- [x] P4-55  dash_render.py: security — base64 encoding of data payload prevents special chars (quotes, backslashes, newlines) in data from breaking generated Python file syntax
- [x] P4-56  dash_render.py: security — `allow_websocket_origin` restricted to `['localhost:{port}']`; no wildcard

### Python Unit Tests — Phase 4

- [x] P4-57  test/test_server.py: `ServerAppBuilder.build()` on minimal 1-graph spec → output file compiles without error (`compile(source, '', 'exec')`)
- [x] P4-58  test/test_server.py: generated file contains `def make_document(doc):` definition
- [x] P4-59  test/test_server.py: generated file contains `if __name__ == '__main__':` block
- [x] P4-60  test/test_server.py: generated file contains `Server` and `allow_websocket_origin` strings
- [x] P4-61  test/test_server.py: `make_document` importable from generated file — call it with a Bokeh `Document()`; assert `doc.roots` is non-empty
- [x] P4-62  test/test_server.py: filter callback correctly recomputes histogram CDS — verify `top` array changes when filtered to half the rows
- [x] P4-63  test/test_server.py: filter callback correctly recomputes lfit CDS — verify `y` values change when filtered to subset
- [x] P4-64  test/test_server.py: filter callback updates KPI Div.text — verify mean recomputes from filtered DataFrame
- [x] P4-65  test/test_server.py: brush callback updates brush-mode KPI Div.text — verify mean from selection indices
- [x] P4-66  test/test_server.py: base64-encoded data round-trips correctly — encode → decode → same DataFrame
- [x] P4-67  test/test_server.py: `title("<script>alert(1)</script>")` — verify generated file does not contain unescaped `<script>` tag
- [x] P4-68  test/test_server.py: data column containing Python string escape chars (`\n`, `\'`) — generated file still compiles without SyntaxError
- [x] P4-69  test/test_server.py: `--mode standalone` with existing spec → still produces valid HTML file (regression)
- [x] P4-70  test/test_server.py: `_compute_histogram` returns dict with keys top/left/right; len(top) == bins
- [x] P4-71  test/test_server.py: `_compute_kpi` for stat='mean' returns correct mean; stat='dcount' returns unique count
- [x] P4-72  test/test_server.py: `_compute_lfit` returns 100 x-points and corresponding y-points

### Certification Scripts (Stata) — Phase 4

- [x] P4-73  test/test_e2e_serve.cscript: write cscript header and Python/jsonio availability checks (same pattern as test_e2e_single.cscript)
- [x] P4-74  test/test_e2e_serve.cscript: `dash serve` with empty registry → rc==198 and error message contains "no graphs registered"
- [x] P4-75  test/test_e2e_serve.cscript: `dash serve, port(99999)` after registering a graph → rc==198
- [x] P4-76  test/test_e2e_serve.cscript: `dash serve, port(0)` → rc==198
- [x] P4-77  test/test_e2e_serve.cscript: `dash serve, port(abc)` → rc==198
- [x] P4-78  test/test_e2e_serve.cscript: `dash build, saving(t.py) server` → `.py` file created; confirm file exists
- [x] P4-79  test/test_e2e_serve.cscript: verify generated `.py` file is syntactically valid Python using `python: import ast; ast.parse(open(path).read())`
- [x] P4-80  test/test_e2e_serve.cscript: verify generated `.py` file contains string "make_document"
- [x] P4-81  test/test_e2e_serve.cscript: verify generated `.py` file contains string "Server"
- [x] P4-82  test/test_e2e_serve.cscript: verify generated `.py` file contains string "allow_websocket_origin"
- [x] P4-83  test/test_e2e_serve.cscript: call `make_document` on a Bokeh `Document()` from within `python:` block; assert no exception; assert document has at least one root

### Adversarial Tests — Phase 4

- [x] P4-84  test/test_adversarial.cscript: add test — `dash serve, port(5006); import os` — semicolon in port value → rejected by integer regex
- [x] P4-85  test/test_adversarial.cscript: add test — KPI title `"<script>alert(1)</script>"` in server mode → HTML-escaped in generated Div.text; `<script>` not present unescaped
- [x] P4-86  test/test_adversarial.cscript: add test — data value containing `'); exec('id')` → base64-encoded; verify generated .py file compiles cleanly

### SMCL Help Updates — Phase 4

- [x] P4-87  dash.sthlp: add `dash serve` to Syntax section with options port(), nobrowser, timeout()
- [x] P4-88  dash.sthlp: add `server` option to `dash build` Syntax section
- [x] P4-89  dash.sthlp: add "Server Mode" section explaining blocking behavior, Ctrl+C to stop, what it enables vs standalone
- [x] P4-90  dash.sthlp: add comparison table: standalone vs server capabilities (KPI recompute, histogram recompute, all glyphs in brush, deployment model)
- [x] P4-91  dash.sthlp: add Phase 4 example to Examples section showing `dash serve` workflow
- [x] P4-92  dash_setup.sthlp: add note that Bokeh Server uses Tornado (bundled with Bokeh >=3.0); no additional installation required

---

## PHASE 5 — NEW PLOT TYPES & BUG FIXES

### Phase 3 — Easy New Plot Types (dropline, rcapsym, scatteri)

- [x] P5-01  dash_parse.mata: add dropline, rcapsym, scatteri to `_is_supported_plot()`
- [x] P5-02  dash_parse.mata: add abbreviations: dr→dropline; scatteri, rcapsym exact match
- [x] P5-03  dash_parse.mata: for scatteri — validate all varlist words are numeric; require even count; build JSON "values" array
- [x] P5-04  dash_parse.mata: for rcapsym — add to range-plot branch (yvar1 yvar2 xvar)
- [x] P5-05  dash_render.py: GlyphMapper.map_dropline — segment(x,0→x,y) + scatter; return [seg, dot]
- [x] P5-06  dash_render.py: GlyphMapper.map_rcapsym — rcap spine + 2 end caps + 2 scatter markers; return 5 renderers
- [x] P5-07  dash_render.py: GlyphMapper.map_scatteri — inline ColumnDataSource from "values" list; return [scatter]
- [x] P5-08  dash_render.py: standalone dispatch — dropline in _add_glyph(); rcapsym in range_dispatch; scatteri in _make_figure() special branch
- [x] P5-09  dash_render.py: server dispatch — dropline, rcapsym, scatteri elif branches in _generate_app_source()
- [x] P5-10  test/test_glyphs.py: map_dropline returns [seg, scatter]; seg drops to y=0
- [x] P5-11  test/test_glyphs.py: map_rcapsym returns 5 renderers [spine, cap, cap, dot, dot]
- [x] P5-12  test/test_glyphs.py: map_scatteri renders inline coords; empty values → empty renderer
- [x] P5-13  test/test_pipeline_integration.py: dropline, rcapsym, scatteri full pipeline tests
- [x] P5-14  test/test_server.py: dropline, rcapsym, scatteri server dispatch tests

### Phase 4 — Medium New Plot Types

- [x] P5-15  dash_parse.mata: add pcspike, pcarrow, pcbarrow with 4-var parsing (y1var x1var y2var x2var)
- [x] P5-16  dash_parse.mata: add tsline, tsrline, mspline as standard/range types
- [x] P5-17  dash_parse.mata: add function with expression parsing (collect all tokens, validate chars)
- [x] P5-18  dash_render.py: GlyphMapper.map_pcspike — segment(x0=x1,y0=y1,x1=x2,y1=y2)
- [x] P5-19  dash_render.py: GlyphMapper.map_pcarrow — segment shaft + Arrow(OpenHead) per row
- [x] P5-20  dash_render.py: GlyphMapper.map_pcbarrow — segment shaft + Arrow(NormalHead both ends) per row
- [x] P5-21  dash_render.py: GlyphMapper.map_tsline — delegates to map_line
- [x] P5-22  dash_render.py: GlyphMapper.map_tsrline — delegates to map_rline
- [x] P5-23  dash_render.py: GlyphMapper.map_mspline — PchipInterpolator 200-point smooth line
- [x] P5-24  dash_render.py: GlyphMapper.map_function — AST-whitelisted expression evaluator (NEVER raw eval)
- [x] P5-25  dash_render.py: standalone dispatch — PC types via _add_pc_glyph(); tsline/mspline in dispatch; tsrline in range_dispatch; function in _make_figure() special branch
- [x] P5-26  dash_render.py: server dispatch — pcspike/pcarrow/pcbarrow/tsline/tsrline/mspline/function in _generate_app_source()
- [x] P5-27  dash_render.py: extend _VK and _VAR_KEYS with y1var/x1var/y2var/x2var for PC type variable collection
- [x] P5-28  test/test_phase4_plots.py: 70 tests covering all 7 new plot types

### Phase 5 — Missing Abbreviations & Bug 5

- [x] P5-29  dash_parse.mata: add mlp→mlabposition, mlg→mlabgap, mlw→mlabwidth
- [x] P5-30  dash_parse.mata: add fc→fcolor, fi→fintensity, asp→aspectratio
- [x] P5-31  dash_parse.mata: add abbreviations for Phase 3-4 plot types (dr, tsl, tsrl, msp, func)
- [x] P5-32  dash_render.py: DashRenderer._apply_graph_filter — apply per-graph if_expr/in_expr
- [x] P5-33  dash_render.py: _make_source — accept optional df= parameter for filtered slice
- [x] P5-34  dash_render.py: _setup_sources — call _apply_graph_filter for each non-linked graph
- [x] P5-35  test/test_phase5.py: in_expr '1/10' → 10 rows; if_expr 'y > 10' → filtered rows
- [x] P5-36  test/test_phase5.py: injection in if_expr blocked; two graphs with disjoint filters
- [x] P5-37  test/test_phase5.py: _apply_graph_filter unit tests (in_expr slicing, if_expr equality)

### HTML Output Validation Tests

- [x] P5-38  test/test_html_output.py: HTML structure tests — doctype, Bokeh root, script tags, JSON data
- [x] P5-39  test/test_html_output.py: per-plot-type tests — scatter/line/histogram/bar/spike/lfit/rarea/dropline/mspline/function HTML contain correct glyph type names
- [x] P5-40  test/test_html_output.py: XSS safety — <script> in title escaped in HTML output
- [x] P5-41  test/test_html_output.py: CSP meta tag present in output HTML

---

## PHASE 6 — GRAPH OPTIONS APPLICATION

Previously-parsed graph options (xtitle, ytitle, aspectratio, note, caption, legend) were stored in JSON but never forwarded to the Bokeh figure. This phase wires them all up.

### Implementation

- [x] P6-01  dash_render.py: apply xtitle → fig.xaxis.axis_label (HTML-escaped; XSS-safe); fall back to variable label when absent
- [x] P6-02  dash_render.py: apply ytitle → fig.yaxis.axis_label (same escaping and fallback)
- [x] P6-03  dash_render.py: apply aspectratio → fig.aspect_ratio (float parse; invalid values silently ignored)
- [x] P6-04  dash_render.py: apply note → bokeh.models.Label added to fig.below ("below" region annotation)
- [x] P6-05  dash_render.py: apply caption → bokeh.models.Label added to fig.below (coexists with note)
- [x] P6-06  dash_render.py: apply legend(off) → fig.legend.visible=False; legend(top/bottom/left/right) → legend.location

### Tests (test/test_graph_options.py)

- [x] P6-07  xtitle sets x_axis_label; XSS-escaped; absent → variable label fallback
- [x] P6-08  ytitle sets y_axis_label; XSS-escaped; absent → variable label fallback
- [x] P6-09  aspectratio=1.5 → fig.aspect_ratio≈1.5; invalid → no crash; absent → None
- [x] P6-10  note creates Label in fig.below with correct text; XSS-escaped
- [x] P6-11  caption creates Label in fig.below; note+caption coexist (≥2 labels)
- [x] P6-12  legend(off) sets visible=False; absent → no crash

### Remaining / Not Yet Implemented

- [x] P6-15  Server-mode (generated .py) application of xtitle/ytitle/aspectratio/note/caption — _generate_app_source() now reads these from graph_options and applies them; tests in test_server.py::TestServerGraphOptions
- [x] P6-16  Bug fix: xline/yline string keys (from Mata parser) not matching xline_values/yline_values (legacy list keys) expected by renderer — fixed via _parse_refline() helper; tests in test_graph_options.py::TestXlineYline (5 tests)

### Remaining / Not Yet Implemented

- [ ] P6-13  xlabel(numlist, ...) / ylabel(numlist, ...) — custom axis tick values and labels via FixedTicker + FixedTickFormatter (requires parsing Stata numlist syntax)
- [ ] P6-14  legend label overrides from legend() string list — currently only position/off handled; per-renderer label strings not yet wired up
