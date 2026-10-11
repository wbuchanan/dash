# UltraPlan Research: dash — close 22 GAPS2 gaps

> Generated: 2026-09-25
> Phase: 2/6 - RESEARCH
> Research topics extracted: 12
> Subagents deployed: 5 (3 codebase, 1 web, 1 Stata docs)
> Full reports (cited below as [A], [B], [C], [W], [D]):
> - [A] `.ultraplan/research/codebase-axes-text-legend-colour.md` — B1, B2, B3, B5, B6, B7, G16, X2, D1
> - [B] `.ultraplan/research/codebase-formats-filters-histogram-parity.md` — E1, E3, G6, X1, E2, C2, E14
> - [C] `.ultraplan/research/codebase-stata-serve-setup-tracking.md` — G1, G2, G3, G5, F1, K2, tracking, test infrastructure
> - [W] `.ultraplan/research/web-bokeh-ecmascript-python.md` — Bokeh 3.8/3.9 APIs, ECMAScript, Python, Tornado, Chrome
> - [D] `.ultraplan/research/docs-stata-rules.md` — Stata's own rules, cited to `/Applications/StataNow/ado/base/` file:line
>
> Tree state: every anchor was checked at HEAD `91d97be` on `s3-bugs`, the audit commit. No source file has changed since, so GAPS2's line numbers hold to within a few lines except where noted.

---

## Research Topics

| # | Topic | Source category | Priority |
|---|---|---|---|
| 1 | Current code anchors for all 22 gaps | Q1, Q2 | high |
| 2 | Stata display-format rules (%w.dg, c, comma, %t pictures) | Q6 | high |
| 3 | numlist grammar; axis label and scale rules | Q2 (B1/B2) | high |
| 4 | Textbox, title, legend option grammar and abbreviations | Q2 (B3/B5/B6/B7) | high |
| 5 | Bokeh 3.8/3.9 APIs: LegendItem, overrides, JS formatters, Select, ranges | Q5, Q10, Q14 | high |
| 6 | Histogram edge rule | C2 | medium |
| 7 | Scheme-file grammar; colorvar rules | D1, Q5 | medium |
| 8 | Filter callback architecture, both modes; node harness state | Q10, Q15 | high |
| 9 | Served template, dimming, bs reflow | Q11 | medium |
| 10 | Launcher, argparse, /health; version floor | Q8, Q12 | medium |
| 11 | Stata-side parsers, cell cap, name checks, internal columns | Q7, Q9, Q16 | high |
| 12 | Tracking formats and the tests that guard them | Q4, Q21, Q23 | high |

---

## Codebase Analysis

**Type:** existing codebase (Stata package, two renderers).

**Stack measured [C]:**

| Interpreter | Python | bokeh | pandas | numpy |
|---|---|---|---|---|
| Stata's `c(python_exec)` = `/opt/anaconda3/bin/python3` | 3.13.9 | 3.8.0 | 2.3.3 | 2.3.5 |
| Development `python3` (homebrew) | 3.14.5 | 3.9.0 | 3.0.1 | 2.4.3 |

`make test` runs pytest under Stata's Python (`DASH_STRICT=1 DASH_BASELINE=stata`), `make test-dev` under the development one, `make cert` the cscripts under Stata's Python. conftest's `_BASELINES` pins both. node v24.13.1 is installed; headless Chrome is found by `test/responsive_probe.py` (`DASH_CHROME` override), skipped when absent.

### Cross-cutting mechanisms every section must respect [A §0, B §1.4]

1. **The served app is assembled by copying.** `ServerAppBuilder` copies module functions and constants by name with `inspect.getsource` (constants 24326-24428, functions 24466-24687; `OptionTranslator`, `SchemeParser`, `GlyphMapper` whole at 24698-24700). Every new module-level helper, table or JS string constant must be added to those lists. Guards: `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`, `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads`.
2. **Every new function needs a named test** in `test/function_test_map.py` (enforced by `test_function_test_map.py`); Stata programs in `test/program_coverage_map.py`.
3. **Naming options in the note.** `_dash_report_suboptions(option, tokens, seen, key)` (18813) with the per-renderer `seen` set; `_dash_warn_once` (12377) for one-off notes. Once an option is honoured it must print nothing (Q22). `test_unsupported_report_is_true.py` fails if a "pending" option actually changes output.
4. **Figure-building order differs between renderers** ([A §0.2] table): the saved renderer styles axis titles before adding second axes, the served template after; the saved renderer limits `DataRange1d.renderers` to primary-source renderers (22314-22330), the served app has no such step; the parity profile records ranges only when numeric so it cannot see this.
5. **Both-mode test helpers to reuse:** `test_natscale_axes._figures`, `test_textbox_multiline._both_modes`/`_drawn`, `test_dual_axis._lone_figure`, `test_suboption_warnings._both`, `test_mode_parity._standalone`/`_served`/`_spec`/`CORPUS`, `conftest.make_data_json(df, value_labels, label_names)`.
6. **Fixtures:** `.git/info/exclude` hides `*.json`/`*.txt`, so a new fixture needs `git add -f`; `test_fixtures_are_committed.py` requires a test to name each fixture. The trailing `python:` block of an extract script must never call Stata and must write a backtick as `\x60`.
7. **Concurrent Stata:** each run gets `cd <dir> && STATATMP=<dir>/tmp/ arch -arm64 /usr/local/bin/stata-mp -b do …` (trailing slash; not the log's directory). Keep concurrent sessions to two or three: many sessions can rewrite `~/.stata19/console/stata19.rc` without `python_exec`, after which every Python cscript SKIPs. Restore with `set python_exec /opt/anaconda3/bin/python3, permanently`.

---

## Findings by Topic

### 1. Stata display-format writer (E1, E3, G6) — [B §1], [D §8], [W §2, §4]

**Current state.** `_parse_stata_numeric_fmt` (839) reads only `%w.d[f|e][c]`; `_stata_numeric_pattern` (870) and `_format_stata_numeric` (892) write `f`/`fc` with Stata's width fallbacks and an `e` branch that ignores width (Stata `%9.3e` of 1234.5678 is `1.23e+03`, dash writes `1.235e+03`). `_dash_load_columns` (635) and the served `_NUM_FORMATS` (24930) keep only `%f` formats, so `%g`/`%e`/`%8.0gc` are dropped. `_dash_format_kpi_value` (19609) takes the date branch first (a date KPI ignores `fmt()`), maps `%9.0g`/"" to Python `:g`, and any other format to Python `format()` with `str(value)` fallback. The JS twin is `dash_numfmt` and friends (14378-14482), driven by `_kpi_js_number_format` (23004). Dates use one fixed picture per kind (`_format_date_value_standalone` 289-332; `_datetime_formatter_for` 335).

**Export.** dash.ado already sends each variable's display format (`_dash_formats_json` 4063-4121 → `build_options.formats`), but not its storage type: `_dash_write_stata_data` (1214) writes `float(x)`, so a float 0.1 arrives as 0.10000000149011612. G6 needs `sfi.Data.getVarType` added to the document and read by both loaders; the test stand-in `FakeSfi` (`test_string_value_export.py:78`) needs a `getVarType`. `dash kpi` validates `fmt()` with `confirm numeric format` (dash.ado 2294-2313), which accepts `%21x`, `%16H`; Stata's own display of each KPI already travels as `"display"` in `kpis_json` (6974): a ready truth value.

**The 14 number-to-text sites** ([B §1.3] table): KPI first paint / after move / after brush (both modes), dropdown labels, slider labels, tooltips and the tooltip fallback, date-axis ticks, numeric axis `format()`, marker labels and `mlabformat()`, by() panel titles, the CSV, colorvar key labels. One formatter must reach all of them; the served app needs the full `bo['formats']` (custom pictures such as `%tdCCYY-NN-DD` are lost today because `date_vars` holds only the kind). Date columns are stored in epoch ms; `_dash_unix_ms_to_unit` (16214) recovers the Stata value (floor for period kinds) and needs a JS twin for period sliders.

**Stata's rules [D §8].** `%w.0g` is documented only by examples; the derived rule (all documented examples agree) is: at most `w-2` significant digits in fixed form, else exponent with a `w-6`-digit mantissa (`%9.0g` 10,000,000 → `1.00e+07`; `%12.0g` 52313712223 → `5.23137e+10`); `%w.dg` with d>0 is "approximately d significant digits" (31415.9265 → 31416); `f` falls back to `g` when too wide; `%9,2fc` gives `1.000,03`; the `0` leading-zero flag applies only to `f`. Date pictures: `%tw` → `CCYY!www`, `%tm` → `CCYY!mnn`, `%tq` → `CCYY!qq`, `%th` → `CCYY!hh`, `%ty` → `CCYY`; `+` prints nothing, `_` a space, `!c` a literal; fractional seconds off by default; times truncate, never round. No stdlib function reproduces `%w.0g` [W §4]; European comma is `format(x, ',.2f').translate(str.maketrans(',.', '.,'))`; never use `Intl`/locale (twin-identical output offline).

**Fixtures on disk.** `date_truth.json` (from `scripts/extract_date_truth.do`) holds 15 numeric formats × 10 values of Stata `display` text and all 8 date kinds; it lacks the European comma, `%x`/`%H`, and custom pictures. `value_truth.json` holds 28 `confirm numeric format` return codes but no display text.

**Tests that pin today's behaviour and will flip [B §1.5]:** `test_dates.py::TestNumericDisplayFormats` (expects `%9.0g` to return None; asserts exactly 56 cases), `test_date_range.py` ~944-958 ("31 Dec 9999" pictures), `@{date}{%F}` pins in `test_date_range.py:609`, `test_served_dates.py:129/229`, `test_help_claims_4.py:1706`; `test_saved_filter_layers.py` (`"2001-12-31 00:00:00"`, `_dash_option_value(1.0) == "1"`); `test_server_layer_defects.py:1080-1101`; `test_adversarial_matrix.py:1664-1695`.

**Security [B §1.4].** The JS KPI card rebuild (14637-14645) concatenates the format into HTML without escaping while the Python card escapes it (`_dash_kpi_card_html` 13629); date pictures carry user text through `!`. Variable formats come from `st_varformat` without the `fmt()` character check. `test_label_sinks.py:855-857` pins tooltip fields to `@\{name\}(?:\{[0-9.,%FT ]+\})?`, which rejects `{custom}`; widen it on purpose and carry the format in `CustomJSHover.args`.

### 2. Axis labels and scales (B1, B2, G16) — [A §B1, §B2, §G16], [D §1-3, §11]

**B1.** `_dash_parse_axis_label_opt` (16041-16074) flattens every token and treats single quotes as delimiters (Stata does not). Its only caller is `_dash_parse_axis_spec` (16605-16735), which feeds xlabel/ylabel, xtick/ytick and xlabel2/ylabel2; `#N`, `none`, `minmax` and `a(b)c` are handled before it. Verified today: `1 "2019" 2 "2020"` → ticks [1,2,2019,2020], no labels; `10 20 to 40` → [10,20,40] with label `{"20.0": "to"}`; `1/5` named and ignored; compound-quoted label → a lone backtick; and `#5 50 "fifty"` drops the `#5` (Stata's grammar is `[rule] [numlist ["label"…]]`, axis_label_options.sthlp:47-55; not listed in GAPS2). **dash.ado already expands numlists** (`_dash_validate_value`, kind `numlist`, 2122-2148, used by `colorcuts` and `range`); the graph-option check loops (2463, 4705) write a normalised value back, so B1's ado step reuses them. The graph-key `foreach` list appears seven times in dash.ado (3951 … 4942): any new graph key goes in all seven. Stata's numlist edge forms [D §1]: `1(2)10` → 1,3,5,7,9; `3/1`, `-5/-8`, `9(-2)1`, `-1(.5)2.5` legal; `1 2 to 4` and `1 2:4` step by the difference; `[b]` ≡ `(b)`; commas separate only inside option parentheses, which collides with the `, suboptions` comma, so sub-options must be split off first. Label values widen the axis unless `norescale` (axis_label_options.sthlp:344-350); `add` merges, a rule replaces. The explicit-label applier (16783-16798) keys `major_label_overrides` by float; Bokeh matches them as JS numbers, so int and float keys are interchangeable but string keys never match [W §1b]; multi-line `\n` labels render; `$$` in a label is parsed as LaTeX.

**B2.** `_dash_apply_scale_ranges` (19017-19065) replaces the range with an exact `Range1d` before any layer is drawn; `_parse_scale_range` (2409) matches only `range(`, so `r()` and `rev` are named; `norescale` is parsed nowhere. Second axes narrow the same way in `_dash_finish_secondary_axes` (17158-17163). The natural place for the hull step is `_dash_finish_count_ticks` (17334), which runs after the layers in both modes; `_dash_count_axes` (17210) collects per-axis entries and `_dash_place_count_ticks` (17276) already widens a `DataRange1d` to its outermost ticks with Bokeh's 5% pad model; `_dash_secondary_values` (17040) returns the finite drawn values through each renderer's view, skipping colour-key swatches. A narrow `Range1d` clips, it does not drop data [W §1g]; `DataRange1d` counts invisible renderers unless `only_visible=True`. Stata's rule: `range()` only expands, `range(#)` is one value, missing values are ignored, `r()` is the abbreviation [D §3]. **Truth already on disk:** `axis_truth.json` probes `b_range_0` (−1.16, 42.16), `b_range_60` (8.58, 61.42), `b_range_narrow` (identical to default: never narrowed), `b_range_0_50` (−1.42, 51.42) hold SVG-fitted drawn extents; no test reads them. The only committed `.Graph` extent reading (`natscale_axes_truth.json._meta`) gives the data range [12, 41], not the drawn extent, and `.Graph` has no `range_min`; candidates are `.Graph.plotregion1.yscale.{min,max,curmin,curmax}` or `.Graph.yaxis1.major.{min,max}` and must be probed [D §11]. `test_axis_options.py::TestAxisScale` pins exact narrowing and will flip.

**G16.** Value labels already reach Python in both modes (`valueLabels`/`valueLabelNames` written at 1313-1351; loaded at 21150 saved and 25699 served; attached to the mapper by `_dash_attach_labels` 18745). The labelset-then-variable lookup is written five times; `GlyphMapper._mlabel_value_labels` (6973) is the cleanest and `_mlabel_value_text` (7085) turns a code into text. `_dash_build_hover` (19839) and `_dash_apply_axis_options` (16965) lack a value-label parameter; the marker-label derived column in `_apply_mlabel_opts` (6732-6765) is the pattern for a hover text column, and derived columns survive filter moves in both modes. `valuelabel` (minimum `val`) is currently named in the note; `test_suboption_warnings.py` pins that and will flip. Stata maps y options through the first y variable's label set and x through the x variable's (axis_label_options.sthlp:269-280).

### 3. Textbox grammar (B3, B6, B7) — [A §B3, §B6, §B7], [D §4]

`_TEXTBOX_SUBOPTS` (2438-2445) holds full names only and omits `bcolor`, `lstyle`, `lalign`, `prefix`, `suffix`, `axis`; `_textbox_split_point` (2484) splits only before a listed name, so `"T", c(red)` becomes the text `T\n,\nc(red)`. `_parse_textbox_opt` (2614-2682) keeps names as written, so `c(red)` never reaches `_textbox_color` (2597) or `_textbox_size` (2577); `_dash_textbox` (18861) names anything outside `{"size","color","colour"}` as written. Stata's minimum abbreviations [A table; D §4]: `tsty:le`, `orient:ation`, `si:ze`, `c:olor`, `j:ustification`, `al:ignment`, `m:argin`, `bc:olor`, `fc:olor`, `ls:tyle`, `lp:attern`, `lw:idth`, `lc:olor`, `la:lign`, `bm:argin`, `bex:pand`, `place:ment`, `pos:ition`; `linegap`, `width`, `height`, `box`, `nobox`, `ring`, `span`, `prefix`, `suffix`, `axis` take no abbreviation; `bcolor`/`fcolor`/`lcolor` are ignored without `box`; there is no `nobexpand`; dash's `colour` and `style` are not in Stata's help. `axis(#)` routing: dash.ado's repeat merge (`_dash_rep_merge`, dash_parse.mata 4826) folds `ytitle("a") ytitle("b", axis(2))` into one `ytitle` before Python sees it, so faithful routing belongs before the merge (`_dash_opts_repeats`/`_dash_rep_reduce`); a Python-side rewrite beside `_dash_lone_second_axes` (1639) is the fallback and must run before that lone-axis rewrite.

**B6.** `_dash_axis_labels` (16036-16037) does `x_text or x_default`; `_dash_textbox('""', 'xtitle')` already returns `''`, so the fix is telling "given as empty" from "absent" (raw non-empty, lines empty). `_dash_lone_second_axes` (1692) keeps `ytitle2("")` because the raw `""` is non-empty.

**B7.** `_dash_add_secondary_axes` (16997-17030) passes the raw `{n}title2` to `LinearAxis(axis_label=…)`; it is the only reader; its signature lacks `seen`/`key` (the template call at 26207 must change too); styling the second axis inside it avoids the renderer-order difference. JSE-46 case `jg46k` (`test_json_escaping.cscript:1974`) already stores a multi-line `ytitle2` as typed.

### 4. Legend order and labels (B5) — [A §B5], [D §5], [W §1a, §1i]

`_dash_apply_legend` (15780-15983) reads `order()` as `re.findall(r"\d+")` applied to positions (15847-15852) and `label()` by displayed position after the reorder (15929-15939); `lastlabel` is not in `_DASH_LEGEND_SUBOPTS` (18839) and is named. `_dash_legend_entries` (19754) skips layers whose renderers are empty or all swatches, so displayed position can drift from Stata's plot numbering; `_dash_plot_style_indices` (19513) gives Stata's numbering with a CI fit counting as two. Stata's precedence [D §5]: `order(# "text")` beats `label()`; `lastlabel()` beats both and indexes by on-graph position; `-` starts a text-only line, `" "` a blank one, `""` nothing. **A label-only `LegendItem` works as-is in Bokeh 3.8 and 3.9** [W §1a]: `renderers=[]` with a value label passes validation and BokehJS draws the text with an empty glyph cell; no placeholder glyph is needed (the invisible-swatch pattern `_DASH_SWATCH_PREFIX` exists if one were). Renaming after construction must use `item.label = value("x")` (a bare string is a field). Callers: `_rebuild_legend` (21794) saved; template 26435 served.

### 5. Histogram edge rule (C2) — [B §3], [D §6]

`GlyphMapper.map_histogram` (9519-9627): the discrete branch (9565-9575) already uses floor and clamp; the continuous branch counts with `np.histogram` (9577) over edges from `_histogram_grid` (9750-9766), which appends an extra edge only when `edges[-1] < a_max - 1e-9·scale`, so a value a few ULPs above the last edge is dropped. Reproduced: nlsw88 ttl_exp `bin(27)`/`bin(51)` count 2245 of 2246; census pop `bin(75)` 49 of 50. The JS recount (14818-14826) drops values outside `[edges[0], edges[last]]`. **The served `_compute_histogram` no longer exists**: the served app redraws through `map_histogram` (`agg['redraw']` 26919), so one mapper fix covers both modes; the agg config (9607-9623) needs `start`, `width`, `bin` so the JS does not rebuild `h` from the edges. dash.ado 3832 lets `start()` within reldif 1e-5 above the minimum through; Stata errors only above that tolerance with "option start() may not be larger than minimum of <var>" r(198), and folds `idx < 0` into bar 0 and `idx == bin` into `bin-1` (twoway__histogram_gen.ado:200-203) [D §6]; default `bin = max(1, int(min(sqrt(N), 10·log10(N))))`, `width()` → ceil, discrete shifts `min` by `h/2`. Truth: `extract_stat_truth.do` layer 1 records bin/start/width/xmin/xmax and non-empty bar heights per dataset × option; `nlsw88:ttl_exp` and `bin(27)`/`bin(75)` are not recorded yet; the CSVs `test/fixtures/data/nlsw88.csv` and `census.csv` are checked in. Tests: `test_statistical_truth.py::TestHistogramAgainstStata` (121-177), `test_statistical_helpers.py::TestFilterJavaScript` (859).

### 6. Scheme quoted values (D1) — [A §D1], [D §9]

`SchemeParser._parse_lines` (3941-3998) takes `tokens[-1]` as the value, so `color background "255 0 0"` lands under a malformed key; `//`, `*!`, `sequence` and `label` lines are not skipped as Stata skips them (`label "s2 color"` is stored under `'label "s2'` in every shipped scheme). Stata's reader (scheme.class:189-226): tabs → blanks, `tokenize`, `args style id stylename`; the value is the **third token** with quotes removed, later tokens ignored, two-token lines are class defaults. `scripts/extract_scheme_truth.py` `SchemeResolver._load` (207-262) already implements third-token reading. Shipped schemes are unaffected by the switch (their only 4+-token lines are `label`); `schemes/sttrans.scheme:47` was transcribed to `#1a476f%20`, which is why sttrans works today. `translate_mcolor`/`parse_color_alpha` already accept unquoted `26 71 111` and `26 71 111 %20`; quoted forms fail; `khaki*0.3`, `hsv`, CMYK are D7's shared work and not in scope beyond what the quote-strip gives. Parse both `"26 71 111 %20"` (sttrans) and `"0 255 0%50"` (colorstyle help) [D §9]. The 129 third-party schemes are machine-local (`~/Library/Application Support/Stata/ado/plus/s/`), 127 with quoted RGB; a committed test must pin a copied `scheme-d3colors.scheme` (`color p1 "31 119 180"` at :301) and skip the PLUS sweep when absent. The served app receives `_SCHEME_PROPS` parsed at build time, so no template change.

### 7. colorvar explicit forms (X2) — [A §X2], [D §7]

`GlyphMapper._apply_colorvar` (6338-6655; only caller `map_scatter` 7229) takes the interval path whatever `colordiscrete` says (6456-6479) with `searchsorted(side="left")` and keeps cuts below the minimum; the continuous path is now 6599-6629 (GAPS2's 6424-6446 is stale). dash.ado declares `COLORDIScrete COLORNlevels COLORCUTs …` (911-913) with rules `colorcuts=numlist,1` (1867-1869); `colorvarminmax`, `colorrule`, `colorstart`, `colorend` sit in Mata's undeclared-take-once table (`_dash_rep_und_tab` 4318-4400); `colorlevels` is in no table and is named through `*`; `zlabel`/`ztitle`/`zscale` are declared nowhere (Stata: `zlab:el`, `zti:tle`, `zsc:ale`). Declaring them means both syntax blocks, both `g_*` sreturn blocks, the seven graph-key `foreach` lists, Mata `_dash_rep_cat` categories, and drawing on the Legend/ColorBar. Stata's rules [D §7]: under `colordiscrete` with `colorcuts()` the listed values are the levels and everything else joins missing in gray; cuts below the column minimum are dropped, the minimum used if all are; `colorlevels(#)` = #−1 equal cuts; `colorvarminmax` adds min and max as cuts and z ticks; `colorcuts` and `colorlevels` may not be combined. `test_help_claims_7.cscript` HC7-02 asserts `colorlevels()` is named and will flip; `rejected_options.json` records twoway rc 0 for `colorlevels(4)`/`colorvarminmax`.

### 8. Filters: exclude() and dropdowns (E2, X1) — [B §2], [W §1f, §2]

**X1.** `_dash_option_value` (17413) integer-rewrites anything that parses as a whole number, strings included; `_dash_dropdown_values` (1806) drops 'nan'/'None'/'NaT'; the saved JS compares `String(col[i]) !== val` (14138); the served `_dash_dropdown_mask` (17669) maps `_dash_option_value` over both sides. **Not in GAPS2:** the saved snapshot `_dash_json_value` (13828-13862) coerces string codes to numbers ('01' → 1.0, 'nan' → None) for `_orig_data`, every graph snapshot and derived snapshots, so after a move a string marker label "007" becomes 7 and `dcount` merges '01' and '1'; the fix must keep string columns as text in every snapshot. Measured today: string codes select the same rows in both modes (the "keeps no row" claim did not reproduce); 5e-05 and 1e21 select nothing on the saved page; `""` is already listed and selectable. **Bokeh `Select` accepts numeric values since 3.4** (`Tuple(AnyRef, String)`, value `AnyRef`, a value→label Map in BokehJS; labels must be unique) [W §1f], so "compare numbers as numbers" needs a per-filter `numeric` flag in `filter_specs_json` (23707-23714), `Number(val)` in JS and float equality in pandas; no string workaround. Thresholds [W §2]: JS `String(x)` goes exponent below 1e-6 and at or above 1e21 (`1e-7`, unpadded); Python repr below 1e-4 and at or above 1e16 (`1e-07`, padded); neither twin may fall back to native stringification.

**E2.** `_dash_excluded` (17975); saved wiring builds one CustomJS per widget (23723-23826) with `all_graph_sources`/`excluded_sources`/`agg_sources`/derived sources each filtered by that widget's exclusions, while the JS masks with all widgets (14186) and writes only the targets it was handed; served `_on_filter_change` (26758-26964) masks with `_all_widgets` and skips `_dash_excluded` targets and excluded KPIs (26948). A link group is one shared source, excluded only when every member is (dash.sthlp 1130-1137, pinned by `test_help_claims_3.py::TestAnExcludedMemberOfALinkGroupIsFilteredWithIt`). Fix outline: per-target mask = AND of the filters whose exclude() does not name it; group mask = AND of filters that do not exclude every member; served: `_dash_frame_filter_mask(df, [w for w in widgets if not _dash_excluded(t, w._dash_exclude, owners)])` cached per exclusion set; saved: pass every target with its exclusion set, one mask per distinct set, all widgets can share one callback. `TestExcludeHoldsWhileItsOwnFilterMoves` is `test_help_claims_3.py:415-497` (served part already chains `tp._fire`).

**Node harness.** `test_saved_filter_layers.py:85-214` already writes node's source data, booleans, Div text and width back into the Python models, so repeated `_run` calls chain; `test_filter_exclude.py:156` and `test_statistical_helpers.py:820` re-encode from unchanged models and lose state. The stateful mode is a generalisation of the first: encode all callbacks' args into one `models` dict, run a list of `{set widget values, run callback}` steps, dump at the end.

### 9. Saved/served presentation (E14) — [B §4], [W §6]

1. Viewport meta: `_dash_served_template` (2169-2195) adds only the CSP; the saved `_CSP_META` (2307-2314) carries the viewport tag; `test_help_claims_4.py:1643` asserts the served page has none (flip). 2. Dimming: `_apply_nonselection_dimming` (21855) is a method and cannot be copied; it needs a module-level function in the copy list; `_NONSELECTION_ALPHA` (0.15) is already copied but unused; `TestTheModesDifferHere.test_a_brush_dims_unselected_points_less_when_served` asserts 0.1 (flip). 3. rspike/rconnected: the served range branch (26012-26024) always builds `_dash_range_source`, a new source per layer, so a selection never reaches it; use the shared source with an IndexFilter view as `_dash_layer_source` (19391) does. 4. Served bs grid: `_dash_bs_grid` (18606) with `_dash_reflow` (17824) has only the 767.98 px stacking rule; the saved CSS (`_DASH_GRID_CSS` 2318-2402) has md spans (768-991), lg spans (992+) and KPI min-heights 130/150/170 (120 below 768); reproducing the md half-row needs per-child CSS on the GridBox (a risk). 5. bs filter bar: saved builds `filter_bar_html + header_html + tabs + grid` (22712-22731); served puts the header first (27242-27263). `test_mode_parity.py` `ALLOWED` key "layout(bs) is standalone markup" (105-139) also covers reading the grid from markup; only its filter/title clause and the check at 1489-1508 change, the key stays. **Also different, not in E14:** `filterposition(left)` (saved bs: header inside the right column, 22699-22711; served: header above both). The Chrome runner widths are 375/768/1440 (not 375/900/1440), `_served_page` renders with `file_html`, not the served template. Chrome's `--headless=new`, `--dump-dom`, `--screenshot`, `--window-size` are all current [W §6].

### 10. Serve launcher and version floor (F1, K2) — [C §5, §6], [W §1h, §3, §5]

**F1.** `_dash_serve_spec` (dash.ado 7252-7345; port refusal 7307-7310; timeout in minutes) and `_dash_serve` (7349-7439) run the launcher through `runpy.run_path` (7438) and check nothing. The launcher (dash_render.py 27670-27715) does `Popen(_cmd)` with no pipes, `wait()`, never reads `returncode`. **Three clamps, not two:** the app's `__main__` (27371), `main()` (27603) and the launcher (27680). **Tests currently require the clamp** and must be inverted: `test_render_cli_port.py:151,161`, `test_resource_limits.py:1279` (parametrised over all three sites), `test_adversarial_matrix.py:860,878`. `_FakeProc` (`test_help_claims_2.py:756`) takes no keyword arguments and has no `returncode`. `/health` is dash's own handler in the generated app (25563-25582, rate-limited 600/min per IP); Bokeh itself offers only the app root or `/metadata` [W §5]. `bokeh serve` prints "Cannot start Bokeh server, port N is already in use" and exits 1; a bare `Server()` raises `OSError` errno 48 (macOS)/98 (Linux). **A socket held on 127.0.0.1 does not block a wildcard bind on macOS**, so the cscript must hold the same address the app binds (dash binds 127.0.0.1). `test_serve_launch.cscript` SRV-17..20 show the stub-`dash_render.py`-on-adopath pattern; real launches are `test_help_claims_1.py:576` and `test_help_claims_5.py:1348` (poll /health, SIGINT).

**K2.** Old minimums live at dash_setup.ado 60/73/146/147/150/285-296, dash_setup.sthlp 40-42/70/80-82, dash.pkg:17, dash.ado 201-210, dash.sthlp 3131-3134, CHANGELOG 330-334. The generated app (header 25198) has no `from __future__ import annotations`; measured [W §3]: 3.8 raises on `list[int]` and `int | None`, 3.9 only on `|`, both import cleanly with the future import, which must follow only the docstring/comments. `CustomJSTicker` appeared in Bokeh 3.6.0; Bokeh floors: 3.0/3.1 ≥ Python 3.8, 3.2-3.4 ≥ 3.9, 3.5-3.9 ≥ 3.10, 3.10.0 (Aug 2026) ≥ 3.12; **Bokeh 3.9.0 removed pandas as a required dependency**, so dash must declare pandas itself; pandas 3 with Bokeh 3.8 is not a Bokeh-tested combination. **Declared floor (Q8): Python 3.13, bokeh 3.8, pandas 2.3, numpy 2.3** = conftest's `stata` baseline. Tests asserting the old minimums: `test_setup_python_gate.cscript`, `test_setup_honesty.cscript` (207-245, 504-550), `test_program_coverage.cscript` PC-19..21, `test_help_claims_8.cscript:786`, `test_help_claims_8.py:1647`.

### 11. Stata-side data handling (G1, G2, G3, G5) — [C §1-4], [D §12]

**G1.** Internal columns in both twins ([C §1.1] table): `_ROW_ID_COLUMN = "__dash_row__"` (2008; overwritten into the user's source at `_make_source` 21416; JS `const ROW_ID` is a literal at 14219 and filled from the constant at 23499), `__dash_pc_row__` and `__mlabel_values__`/`__mlabel_x__`/`__mlabel_y__` (10832-10890, 11544), `__mlabel__{var}` and `__mlabel__{var}__fmt_{hex}` (6750, 6965; a user column of that name is read as label text), `__dashfix<hex>` strL made in the user's data (1296-1301). **Residual not in GAPS2:** `_x_jit`/`_y_jit` (5498) overwrite a user column of that name, and the derived glyph columns `x`, `y`, `x0`, `top`, `count`, `density`… that `_carry_cols` (5573) never overwrites mean `hover()`/`mlabel()` on a user variable of that name read the derived value. The `__dashq` refusal is dash.ado 4255-4261 (r(110), called at 5943 and 6893, documented at dash.sthlp:166-171, tested by `test_qualifier_in_stata.cscript` QS-06); the renderer has its own copy (`_dash_take_qual_columns` 20321-20342; served check 25002) that must widen to `__dash` while still letting `__dashq<k>` through. Layout/model keys containing `__` are already protected by `_dash_reserved_name` (1547).

**G2.** The four parsers: `_dash_parse_varpart_std` (syntax at 1273), `_1v` (1298), `_3v` (1329), `_4v` (1358); `_any` takes literals. **40 plot types, not 38** (WP-22 added `pccapsym`, `pcarrowi`; table at dash_parse.mata 946-985; families dash.ado 2922-2936), 36 of which take variables. Adding `numeric` to the four `syntax` lines gives Stata's own r(109) before any count check, the order twoway uses (`varlist(numeric ts)` at twoway_yxview_parse.class:120). The r(109) wording is in no local document and must be measured [D §12]. `colorvar`, `mlabel`, `hover`, `by` are validated with `unab` (2149-2233), which checks no type. The renderer has no string check on plot columns; a spec-level refusal belongs after `_load_data`, beside `_dash_refuse_oversized` (21100 saved, 24979 served).

**G3.** `_dash_cell_cap` (2724-2754, r(134)) is called at 5920 with `needed_vars` and at 6875 with `all_vars`, both from `_dash_extract_vars` (dash_parse.mata 2114; keys `yvar xvar var … mlabel colorvar wexp`) plus `_dash_extract_qual_vars` (2255). dash.ado has no per-graph "needs rows" record; the inputs exist (`_dash_link_refusal`, `_dash_filter_items`/`_dash_filter_refusal`, the `csv` flag at 7041, `hover` in graph_options). **The renderer refuses again** at `_dash_refuse_oversized` (1121; called 21100 saved, 24979 served) on the whole frame, and **the served app embeds every row** (`_embed_data` 25092), so a relaxed count is safe for the saved page only; the CSV holds every column of `self.df` (23832-23861). The size note is `_report_dataset_size` (973/994) at 24 bytes per cell over the whole frame. `hover()` variables match no export key (BUGS.md:761 records a hover-only variable never serialised; unverified here).

**G5.** `_dash_is_name` (dash_parse.mata 827-840) is ASCII-only and also validates layout and option words (891, 4030, 4123), so filter() needs a separate variable-name check (its caller is 3454); the by() check at 2916 already uses `\p{L}`; the KPI pattern is dash.ado 6094-6097. **Bigger than GAPS2 says:** the renderer's `_DASH_VARNAME_RE` (19207) is ASCII-only and drops a Unicode name in filter parsing (19340, 19362), `_dash_parse_by` (15513; the graph is drawn without panels, with a warning, in both modes) and hover fields (19932, 20022); `_apply_colorvar` has an inline ASCII regex at 6365 that silently draws no colours. `_dash_is_stata_name` (1183-1190: `isidentifier()` and length ≤ 32) is a Unicode-aware check to reuse. Graph and KPI names stay ASCII on purpose (they become global macro names).

### 12. Tracking formats and the tests that guard them — [C §7, §8]

**BUGS.md.** 428 closed, 4 open entries. Entry shape: `- [ ] Title:` then `File Names and Line Numbers` / `Description` / `Suggested fix` / `Resolution`, exactly once each, in order (`test_tracking_documents.py` `_ENTRY`/`_FIELD`). An open entry's Resolution must contain "not fixed|still open|stays open|remains open" and "because" and exactly one `Graded S<n> (WP-NN): <why>`. **`TestNoOpenEntryBlocksARelease` fails pytest on any open S1 or S2 entry.** A closed entry must name a test that exists. **`scripts/release_verdict.py` does not read BUGS.md** (it judges the gate log); the BUGS.md guard is this pytest.

**ROADMAP.md.** WP-27 at 4131; `## Traceability matrix` at 4243 (`| Gap | Title | Sev | WP |`). `_parse_roadmap` reads `**Gaps closed:**` ids matching `^([A-N]\d{0,2})`; once a WP is DONE, `test_every_gap_a_done_package_lists_is_closed_by_it` looks each id up in **GAPS.md** (the 21 September audit), so WP-28's GAPS2 ids under that field would fail; `_matrix_rows` splits on the text "## Traceability matrix" (also matching `###`), and extra rows break the count.

**CHANGELOG.md** sections: `### Results that change`, `### Security`, `### New`, `### Fixed`, `### Changed behaviour (may need your do-files changed)`, `### Removed`, `### Requirements`, plus the WP-27 sections; no test checks the structure.

**GAPS2.md is untracked**; committing it fails `test_packaging.py:411` unless added to `_ROOT_ALSO`.

**Test infrastructure.** `test/cert_helpers.do` has `cert_file_has`, `cert_log_has`, `cert_file_count` (each clobbers `r()`); `_dash_say` lives in dash_parse.mata. `run_all_cscripts.do` registers 65 scripts (`test_cscript_hygiene.py:418` requires registration); `scripts/run_cert_suite.sh` passes only with every script PASS and none SKIP. The release gate (`scripts/run_release_gate.sh` → `release_gate.do`) `net install`s into a scratch PLUS, runs every `examples/*.do`, one page per scheme, checks `adoupdate`; `release_verdict.py` judges its `GATE` lines. **No shared SVG helper exists**; seven scripts carry private ones (`extract_axis_truth.do`, `test_help_claims_8.cscript` `_hc_svg*`, `test_help_claims_2/5/6.cscript`, `test_bug_regressions.cscript` `_br03_svg`, `test_twoway_option_parity.cscript`). `extract_axis_truth.do` is the model: probes registered with `zp id group dataset body opts`, `graph export .svg` and `graph save .gph`, one trailing `python:` block writes the fixture. Exported SVG writes spaces as U+00A0 by default (`nbsp(on)`): normalise before matching text [D §11]. The pytest session lock (conftest 51-138) refuses a second whole-suite run; strict mode turns any skip red.

---

## Library Documentation (Bokeh 3.8/3.9, measured) — [W]

| API | Finding |
|---|---|
| `LegendItem(label=value("x"), renderers=[])` | Draws a label-only row in 3.8 and 3.9; no placeholder needed |
| `Axis.major_label_overrides` | Keys matched as JS numbers (int/float interchangeable; strings never match); `\n` renders; `$$` is LaTeX; works on a secondary `LinearAxis` |
| `CustomJSTickFormatter(code, args)` | `tick`, `ticks`, `index` in scope; datetime ticks are epoch ms; replaces `DatetimeTickFormatter` |
| `CustomJSHover(code, args)` | `value`, `special_vars`, `format` from `@f{…}`; used via `HoverTool.formatters={"@f": hover}` with `@f{custom}` |
| `RangeSlider.format` / `Slider.format` | Accepts a `CustomJSTickFormatter` (`format.compute(value)`, `ticks=[value]`, `index=0`); date sliders take strftime strings, numeric ones numbro |
| `Select.options` / `.value` | Numeric values allowed since 3.4 (`Tuple(AnyRef, String)`); labels must be unique |
| `Range1d` vs `DataRange1d` | A narrow `Range1d` clips; `DataRange1d(start=…)` pins one side; invisible renderers count unless `only_visible=True`; compute the hull in Python for fixture-testable extents |
| Minimum Python by Bokeh | 3.0-3.1 → 3.8; 3.2-3.4 → 3.9; 3.5-3.9 → 3.10; 3.10.0 → 3.12; pandas optional from 3.9.0; `CustomJSTicker` since 3.6.0 |

---

## Conflicts Found

| # | User said (discovery) | Research shows | Recommendation | User decision |
|---|---|---|---|---|
| 1 | Q4: open a BUGS.md entry per gap **up front** | `TestNoOpenEntryBlocksARelease` turns pytest red on any open S1/S2 entry, so 22 open entries break every full run until the last closes; CLAUDE.md rule 4 requires a green full suite before every commit | Record each gap's BUGS.md entry **in its fix commit**, in closed form naming its regression test; WP-28 in ROADMAP.md lists all 22 from the start and is the place the guard sees them "open" | **Resolved: each entry lands closed, in its fix commit** |
| 2 | Q4/Q23: WP-28 in the WP-01..27 style with a traceability entry | `test_tracking_documents.py` resolves a DONE package's `**Gaps closed:**` ids and the `## Traceability matrix` rows against GAPS.md, not GAPS2.md | Extend `test_tracking_documents.py` to read GAPS2.md for X-prefixed and GAPS2 ids (keeps the guard honest), and give WP-28 its own `#### GAPS2 traceability` table; also add GAPS2.md to `test_packaging.py` `_ROOT_ALSO` so it can be committed | **Resolved: teach the tests GAPS2.md** |
| 3 | Q7: reserve `__dash`, refuse r(110); `__mlabel__*` renamed under it | `_x_jit`/`_y_jit` also overwrite a user column, and derived glyph columns (`x`, `y`, `top`, `count`…) are never carried, so a `__dash` rule alone leaves two collision classes | Rename the jitter columns under `__dash` in the same change; record the derived-glyph-column collision as a G1 residual in BUGS.md (those names are Bokeh glyph fields) | **Resolved: rename jitter columns under `__dash`; glyph-field case recorded as a residual** |
| 4 | Q14: B2's axis extents from `.Graph` properties | The only committed `.Graph` reading gives the data range [12, 41], not the drawn extent; `.Graph` has no `range_min`; `axis_truth.json` already holds SVG-fitted drawn extents for four `range()` probes | Take B2's truth from SVG-fitted extents through the shared helper (extending `extract_axis_truth.do`'s method); probe `.Graph.plotregion1.yscale.{min,max,curmin,curmax}` once and use it only if it matches the SVG | **Resolved: SVG-fitted extents; probe `.Graph` once** |

Findings that widen a gap's scope without contradicting a decision (folded into the plan, no question): X1's snapshot coercion of string codes (`_dash_json_value`); G5's ASCII-only renderer regexes; G3's relaxed count applying to the saved page only (the served app embeds every row); the KPI JS card's unescaped format text (security); the `_PLACEHOLDER` tooltip pattern; the three port clamps and the tests that require them; 40 plot types; the `#5 50 "fifty"` rule-plus-list form; B7's second-axis styling order; E14's `filterposition(left)` difference recorded, not fixed.

---

## Summary and Recommendations

### Key architecture decisions

1. **One display-format module with a JS twin**, `dash_fmt`-style, reached by all 14 number-to-text sites; the writer takes the full Stata format string; storage type exported from Stata; `%x`/`%H` refused at build time.
2. **Axis extents computed in Python after the layers are drawn** (in `_dash_finish_count_ticks`), as the hull of drawn data, label/tick positions and `range()` values, so the result is a `Range1d` a fixture can pin in both modes.
3. **Legend keys built by Stata's plot number**, text resolved default → `label(#)` → `order()` text → `lastlabel()`, then selected and ordered; `-` rows are label-only `LegendItem`s.
4. **Per-target filter masks** computed once per distinct exclusion set, in JS and pandas from one rule; dropdown values typed per filter (numeric vs text) with `Select` carrying numeric values.
5. **Truth from Stata, once, through a shared SVG/.Graph cert helper** and per-family `extract_*_truth.do` scripts; the K2 floor is the measured `stata` baseline.
6. **Tracking that keeps the guards green:** BUGS.md entries land closed with their fix; WP-28 carries the open list; `test_tracking_documents.py` learns GAPS2.md.

### Risks identified in research

1. `%w.0g` has no documented algorithm; the derived rule must be pinned by a Stata-measured fixture of a few hundred values, or a wrong rule ships silently (E1/G6).
2. The served bs md half-row needs per-child CSS on a Bokeh `GridBox`, which Bokeh does not expose directly (E14 item 4).
3. Widening `major_label_overrides`/`FixedTicker` extents on log and date axes must not fight `_dash_place_count_ticks` and the by()-panel common scale (B2).
4. The `axis(2)` routing for titles must happen before dash.ado's repeat merge, in Mata (B3).
5. Many existing tests pin the old behaviour (listed per topic above); each must be flipped deliberately in the same commit as its fix, never deleted.
6. Concurrent Stata sessions can drop `python_exec`; parallel section agents must cap their Stata runs.

### Unanswered questions (for Phase 4 review)

1. The exact r(109) wording twoway prints (measured by the G2 cscript at test time).
2. Whether `.Graph.plotregion1.yscale.curmin/curmax` equals the drawn extent (one probe in the B2 extract script).
3. Whether a `hover()` variable no plot draws is exported at all (BUGS.md:761; outside this plan unless G3's counting exposes it).

---

**User Review Status:** approved (2026-09-25)
**User Feedback:** none; four conflicts resolved with the recommended option
**Proceed to Planning:** yes
