# dash — Stata-side hardcoded-value audit

Scope audited: `dash.ado` (1649 lines), `dash_parse.mata` (1033 lines), `dash_setup.ado` (158),
`dash.pkg`, `stata.toc`, `schemes/*.scheme`. Cross-checked against `dash_render.py` (consumer),
`dash.sthlp` (documented surface), and the installed `jsonio` (`~/Library/Application Support/Stata/ado/plus/j/`,
byte-identical to `/Users/billy/Desktop/Programs/Java/StataJSON/jsonio.ado` and `jsonio.jar`).

Severity key: **HIGH** = Stata gives the user a documented way to control this and dash ignores it.
**MEDIUM** = should track the data/state but no direct Stata analogue. **LOW** = acceptable as internal.

---

## 1. Hardcoded JSON defaults in the three master-JSON assemblies

`dash.ado` builds the `build_options` object by string concatenation in three places. The renderer
(`dash_render.py`) reads **only** `build_options` for layout, theme/scheme, link, filter, title,
subtitle, tabs, and filter_position — so anything absent or literal here is unreachable by the user.

### 1a. Immediate-render path — `dash.ado:974`

```stata
local master_json = `"{"graphs": [`json_spec'], "build_options": {"layout": "1 1", "theme": "default"}}"'
```

| key | literal | file:line | should derive from | consequence | sev |
|---|---|---|---|---|---|
| `theme` | `"default"` | dash.ado:974 | the graph-level `scheme()` value already parsed into `graph_options` (dash.ado:264/388/514), else `c(scheme)` | **`dash scatter mpg weight, scheme(economist)` silently renders in s2color.** `scheme()` is accepted by `syntax` (dash.ado:239, 319), expanded from `sch` (dash_parse.mata:243), escaped into `graph_options` (dash.ado:514) — and then **never read**. `dash_render.py:4990-5000` resolves the scheme *exclusively* from `build_options["scheme"]` or `build_options["theme"]`; `grep` finds **zero** reads of `graph_options["scheme"]` anywhere in `dash_render.py`. dash.ado never writes a `"scheme"` key into `build_options` in any of the three paths. | HIGH |
| `layout` | `"1 1"` | dash.ado:974 | not user-settable in this path (no `layout()` on plain `dash`) | Benign for one graph, but it is a literal rather than `"auto"`, so the renderer's auto-layout code path (`dash_render.py:6783`) is never exercised in immediate mode. | LOW |
| `kpis` | **key absent** | dash.ado:974 | n/a (immediate render has no registry) | Renderer falls back to `.get("kpis", [])`. | LOW |
| `link`, `filter`, `title`, `subtitle`, `registry`, `tabs`, `filter_position` | **keys absent** | dash.ado:974 | n/a in this path | No user option exists on plain `dash` for these, so absence is consistent; documented here for completeness. | LOW |

### 1b. `dash build` — `dash.ado:1433`

```stata
local master_json `"{"graphs":[...],"kpis":[...],"build_options":{"layout":"`layout'","link":"`link'","filter":"`filter_json'","theme":"`theme'","title":"`_title_esc'","subtitle":"`_subtitle_esc'","registry":"`registry'","tabs":"`_tabs_esc'","filter_position":"`filterposition'"}}"'
```

This is the only path where `build_options` is genuinely user-driven. The literals are the **defaults**:

| key | literal default | file:line | should derive from | consequence | sev |
|---|---|---|---|---|---|
| `theme` | `"default"` | dash.ado:1282 | `c(scheme)` (see §5) | A user with `set scheme economist` in `profile.do` gets s2color. `theme()` must be typed explicitly every time. | HIGH |
| `layout` | `"auto"` | dash.ado:1221 | fine as a default | — | LOW |
| `filter_position` | `"top"` | dash.ado:1234 | fine as a default | — | LOW |
| `scheme` | **key never emitted** | dash.ado:1433 | `graph_options["scheme"]` / `theme()` | `dash_render.py:4993` prefers `build_options["scheme"]`; dash.ado never writes it, so the only channel is `theme()`, which is first passed through `_THEME_SCHEME_MAP` (`dash_render.py:4983-4989`, 5 entries: default/clean/mono/economist/sj) before falling through to a raw pass-through. | MEDIUM |

Note: `dash build` has **no `scheme()` option at all** (`syntax` at dash.ado:1174-1185). Users must
discover that `theme()` is the scheme knob; `dash.sthlp:709` documents `scheme(schemename)` as a
graph-level option that (per 1a) does nothing.

### 1c. `dash serve` — `dash.ado:1603`

```stata
local master_json `"{"graphs":[...],"kpis":[...],"build_options":{"layout":"auto","link":"","filter":"","theme":"default","title":"","subtitle":"","registry":"`registry'"}}"'
```

**Every single build option is a baked-in literal.** `_dash_serve`'s `syntax` is
`[, PORT(string) NOBROWSER TIMEOUT(string)]` (dash.ado:1488) — there is no way to supply any of these.

| key | literal | file:line | should derive from | consequence | sev |
|---|---|---|---|---|---|
| `layout` | `"auto"` | dash.ado:1603 | a `layout()` option on `dash serve` (mirrors `dash build`) | **Grid, `name:row,col` placement and Bootstrap (`bs:`) layouts are impossible in server mode.** | HIGH |
| `link` | `""` | dash.ado:1603 | a `link()` option | **Linked brushing cannot be enabled in server mode**, even though `dash.sthlp:420` advertises brush/linking as a server feature. | HIGH |
| `filter` | `""` | dash.ado:1603 | a `filter()` option (the `_dash_extract_filters` Mata helper already exists, dash_parse.mata:874) | **Filter widgets cannot be created in server mode** — the headline reason to use a Bokeh server. | HIGH |
| `theme` | `"default"` | dash.ado:1603 | `theme()` / `c(scheme)` | Server dashboards are always s2color. | HIGH |
| `title` | `""` | dash.ado:1603 | a `title()` option | Server dashboards are always untitled. `dash_render.py:7830` reads `bo.get("title","")`. | HIGH |
| `subtitle` | `""` | dash.ado:1603 | a `subtitle()` option | Same. | HIGH |
| `tabs` | **key absent** | dash.ado:1603 | a `tabs()` option | Tabbed layouts unavailable in server mode. | MEDIUM |
| `filter_position` | **key absent** | dash.ado:1603 | a `filterposition()` option | Renderer defaults to `"top"` (dash_render.py:7366). Moot while `filter` is hardcoded empty. | MEDIUM |

### 1d. Other literals in the same region

| item | literal | file:line | note | sev |
|---|---|---|---|---|
| render mode | `"standalone"` | dash.ado:124, 1461 | correct as a default; `server` flips it at 1462. | LOW |
| KPI `update` | `"filter"` | dash.ado:1093 | reasonable default. | LOW |
| serve `port` | `"5006"` | dash.ado:1490 | Bokeh's own default; reasonable. | LOW |
| serve `timeout` | `"0"` | dash.ado:1491 | reasonable. | LOW |
| `render_py` last-resort path | `` `c(sysdir_plus)'d/dash_render.py`` | dash.ado:998, 1457, 1623 | This one *is* environment-derived. Good. | LOW |

---

## 2. `metaprint()` on the three `jsonio` calls

The three call sites are **byte-identical**:

- `dash.ado:959-961` (immediate render)
- `dash.ado:1375-1377` (`dash build`)
- `dash.ado:1558-1560` (`dash serve`)

```stata
quietly jsonio out `needed_vars', ///
    what(all) filenm("`data_json_path'") ///
    metaprint(varnames varlabels vallabs labelnames)
```

### What is requested
`varnames`, `varlabels`, `vallabs`, `labelnames`.

### What is NOT requested
**Display formats.** No `%td`, `%tc`, `%tm`, `%9.0fc`, `%9.2f`, `%-20s` — nothing format-related.

### Finding 2a — `metaprint()` is a complete no-op here (verified)

`jsonio out` forwards `metaprint` as `passthru` to `jsonout` (jsonio.ado:34, 49). `jsonout` gates the
metadata branch on:

```stata
// jsonio.ado:238
if inlist(`"`metaprint'`filenm'"', "varlabels", "varnames", "vallabs", "labelnames") {
```

It concatenates `metaprint` **and** `filenm` and requires the result to equal exactly one of four
single words. dash always passes a non-empty `filenm()` **and** four space-separated words in
`metaprint()`, so this condition is **never true**. Control falls to the `else` branch, where
`what == "All"` and `filenm != ""` selects `javacall org.paces.Stata.JSON.StataJSON printAllToFile`
(jsonio.ado:~290). The `metaprint()` argument dash passes is therefore discarded entirely; only
`what(all)` has any effect.

Verified against the *installed* copy: `~/Library/Application Support/Stata/ado/plus/j/jsonio.ado`
is byte-identical (`diff -q`) to the repo source, and `jsonio.jar` likewise.

### Finding 2b — `what(all)` cannot emit display formats (verified)

`printAllToFile` serialises `org.paces.Stata.JSON.StataAllToJSON`. Verified two ways:

1. Source `@JsonPropertyOrder` (StataAllToJSON.java:18-21):
   `dataSource, values, firstRecordId, lastRecordId, numberRecords, variableIndices, numberVariables,
   variableIsString, variableNames, variableLabels, valueLabelNames, valueLabels`.
2. `javap -cp jsonio.jar org.paces.Stata.JSON.StataAllToJSON` on the **shipped jar** — same field set,
   no format-related member or getter.

No display-format key exists in the emitted JSON.

### Finding 2c — jsonio *has* the capability internally but never exposes it (verified)

`javap -cp jsonio.jar`:

```
org.paces.Stata.MetaData.Variables:
  protected org.paces.Stata.Variables.VarDisplay displayFmt;
  public org.paces.Stata.Variables.VarDisplay getDisplayFmt();
  public java.lang.Boolean isDateTime(java.lang.String);

org.paces.Stata.Variables.VarDisplay:
  public java.util.Map<String,String> getValues();
  public java.lang.String getValue(java.lang.String);
  public java.lang.Boolean isDate(java.lang.String);
  public java.util.List<Boolean> areDate();
```

So the format map and a date/time predicate exist, but:
- `StataAllToJSON` has no `@JsonProperty` for `displayFmt` (so `what(all)` drops it), and
- `StataMetaToJSON.metaToJSON`'s `switch` (StataMetaToJSON.java:95-120) has cases only for
  `varlabels`, `varnames`, `vallabs`, `labelnames` — **there is no `formats` case to request**.

**Conclusion: jsonio as shipped cannot emit display formats through any option.** dash would need a
separate mechanism (e.g. a Stata-side loop emitting `{"fmt":{"`v'":"`: format `v''"}}` into the spec
JSON, plus `c(dirsep)`/`c(current_date)`-independent SIF-epoch metadata) — this is not a matter of
adding a word to `metaprint()`.

### Finding 2d — consequences (verified against the renderer)

`dash_render.py` consumes only `variableLabels` (5068, 8025), `valueLabels` (5071, 8027),
`valueLabelNames` (5074, 8026) and `variableNames` (8024). Therefore:

| what is lost | consequence | sev |
|---|---|---|
| `%td`, `%tc`, `%tm`, `%tq`, `%th`, `%ty` | Every date/datetime variable arrives in Python as a raw Stata SIF integer. A `%td` birthdate plots as `~22000`; axes show integers; hover tooltips show integers; `filter()` range sliders on a date variable are sliders over integers. There is no `DatetimeTickFormatter` anywhere because there is no way to know the variable is a date. | HIGH |
| `%9.2f`, `%9.0fc`, `%12.0gc`, `%8.3f` | Every numeric display format the user set with `format` is discarded. Axis ticks and hover values fall back to Bokeh defaults; thousands separators, fixed decimals and scientific formats are lost. | HIGH |
| `%-20s`, `%20s` | String display widths lost (cosmetic). | LOW |
| value-label **order**/gaps | `valueLabels` is `Map<String, Map<Integer,String>>` — ordering is not guaranteed by the JSON. Not a hardcoding issue, flagged as adjacent risk. | LOW |

**Explicitly not verified:** I could not run Stata, so I did not empirically execute
`jsonio out mpg, what(all) metaprint(...)` and inspect the file. The conclusions above are from
reading the installed `jsonio.ado` control flow and disassembling the installed `jsonio.jar`.

### Finding 2e — no `if`/`in` on the jsonio calls

All three sites export **all rows** (dash.ado:944-950 documents this as deliberate). There is no row
cap, no `c(maxvar)`/`c(max_N_theory)` consultation and no size warning; the data JSON is then
base64-embedded into the HTML (`dash_render.py:_embed_data`). The committed artefacts in the repo
(`comprehensive_demo.html` = 2.2 MB, `full_dashboard.html` = 1.6 MB) are for the 74-observation
`auto` dataset. MEDIUM — resource-exhaustion surface, not strictly a hardcoding issue.

---

## 3. Hardcoded validation lists, regexes, clamps and limits

### 3a. Plot-type list — `dash_parse.mata:126-166` (`_expand_plottype_str`)

Structure: a flat chain of `==` string equality tests. **It is exact-match only** — it accepts one
arbitrary short form plus the full name and rejects every intermediate prefix. Stata accepts *every*
prefix from the minimum length upward.

| plot type | dash accepts (mata:line) | dash **rejects** (Stata accepts) | sev |
|---|---|---|---|
| scatter | `sc`, `scatter` (127) | `sca`, `scat`, `scatt`, `scatte` | HIGH |
| line | `li`, `line` (128) | `lin` | HIGH |
| connected | `con`, `connected` (129) | `conn`, `conne`, `connec`, `connect`, `connecte` | HIGH |
| area | `ar`, `area` (130) | `are` | HIGH |
| bar | `ba`, `bar` (131) | — | LOW |
| spike | `sp`, `spike` (132) | `spi`, `spik` | HIGH |
| lfit | `lfi`, `lfit` (133) | — | LOW |
| qfit | `qfi`, `qfit` (134) | — | LOW |
| lowess | `low`, `lowess` (137) | `lowe`, `lowes` | MEDIUM |
| lpoly | `lpo`, `lpol`, `lpoly` (138) | — | LOW |
| fpfit | `fp`, `fpf`, `fpfit` (140) | `fpfi` | MEDIUM |
| histogram | `hist`, `histogram` (142) | `histo`, `histog`, `histogr`, `histogra` | MEDIUM |
| kdensity | `kde`, `kdensity` (143) | `kden`, `kdens`, `kdensi`, `kdensit` | MEDIUM |
| dropline | `dr`, `dropline` (151) | `drop`, `dropl`, `dropli`, `droplin` | HIGH |
| tsline | `tsl`, `tsline` (158) | `tsli`, `tslin` | MEDIUM |
| tsrline | `tsrl`, `tsrline` (159) | `tsrli`, `tsrlin` | MEDIUM |
| mspline | `msp`, `mspline` (160) | `mspl`, `mspli`, `msplin` | MEDIUM |
| function | `func`, `function` (163) | `fu`, `fun`, `funct`, `functi`, `functio` | MEDIUM |
| lfitci/qfitci/lpolyci/fpfitci/rarea/rbar/rspike/rcap/rline/rconnected/rcapsym/rscatter/dot/pcspike/pcarrow/pcbarrow/pci/pcscatter/mband/scatteri | **full name only** (135-136, 139, 141, 144-150, 152-157, 161-162, 164) | every abbreviation | MEDIUM |

**Plot types absent from the list entirely** (Stata `twoway` supports them):
`pccapsym`, `pcarrowi`, `contour`, `contourline`, `histogram`'s `twoway` sibling `hist` variants are
covered, `rbarm` (not a twoway type — excluded). Failure mode for these is dash.ado:551-557
(`unrecognised plot type`, `exit(198)`).

The hardcoded error message at **dash.ado:551-557** duplicates the list as prose. I diffed the two:
both enumerate the same 38 types, so they are currently in sync — but they are two independent
hardcodings that must be kept in sync by hand. MEDIUM (maintenance).

### 3b. Option-abbreviation table — `dash_parse.mata:179-253` (`_expand_optkey`) — see §4

### 3c. KPI statistic list — `dash.ado:1080`

```stata
local valid_stats "mean sum count dcount min max median sd p25 p50 p75"
```

| aspect | detail | sev |
|---|---|---|
| Missing statistics Stata's `summarize`/`tabstat` provide | `var`/`variance`, `cv`, `semean`, `skewness`, `kurtosis`, `iqr`, `range`, `first`, `last`, `N` (only `count` = `r(N)`) | MEDIUM |
| Percentiles frozen | `_pctile ... , p(25 50 75)` at **dash.ado:1115** — `p1`, `p5`, `p10`, `p90`, `p95`, `p99` cannot be requested although `_pctile` supports arbitrary `p()`. The regex at 1073 (`[a-zA-Z0-9]+`) would happily parse `p90(...)`; the list rejects it. | MEDIUM |
| `count` semantics | `count` = `r(N)` from `summarize` = count of **non-missing**, not `_N`. Undocumented in `dash.sthlp`. | LOW |
| `dcount` | `codebook` `r(unique)` — `codebook` is slow on large N; no `duplicates`/`levelsof` fast path. | LOW |

### 3d. KPI display value — `dash.ado:1121-1125`

```stata
local kpi_display = "`kpi_value'"
if "`fmt'" != "" { local kpi_display : display `fmt' `kpi_value' ... }
```

| literal/behaviour | should derive from | consequence | sev |
|---|---|---|---|
| no-`fmt()` fallback is the raw macro coercion of `r(mean)` | `: format `kpi_var''` — the variable's own Stata display format | `dash kpi mean(price), title(...) name(k1)` renders `6165.256756756757`. If the user had `format price %9.0fc`, dash ignores it. | HIGH |
| `fmt()` is applied only in Stata at registration time | — | The KPI is also recomputed **in the browser** on filter/brush (`update(filter|brush|both)`); the live-recomputed value has to be re-formatted in Python from the `"fmt"` string that *is* passed through (dash.ado:1421, 1599). That pathway exists; the *default* does not. | — |

### 3e. Name-length / name-shape limits

| file:line | regex | limit | vs. Stata | sev |
|---|---|---|---|---|
| dash.ado:857 | `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$` | graph `name()` ≤ 32 chars, ASCII only | Length matches Stata's 32-char name limit. **But Stata 14+ permits Unicode characters in names**; this regex rejects them. | MEDIUM |
| dash.ado:1088 | `^[a-zA-Z_][a-zA-Z0-9_]{0,31}$` | KPI `name()` ≤ 32, ASCII only | same | MEDIUM |
| dash.ado:1073 | `^([a-zA-Z0-9]+)\(([a-zA-Z_][a-zA-Z0-9_]*)\)$` | KPI statspec | ASCII varnames only; also anchored so `mean( mpg )` (spaces inside parens) fails with a misleading "syntax is stat(varname)" error. | MEDIUM |
| dash.ado:1351 | `^[a-zA-Z_][a-zA-Z0-9_]*$` | filter-variable name sniff | ASCII only; a Unicode-named variable in `filter()` is **silently dropped** from `all_vars` (no error) → the filter widget vanishes without a message. | HIGH (silent) |
| dash_parse.mata:786, 845 | `^[a-zA-Z_][a-zA-Z0-9_]*$` | `by()` / `if_expr` variable extraction | ASCII only; Unicode-named variables in `if` or `by()` are never serialised. | MEDIUM |
| dash.ado:867 | `name\([^)]*,[ \t]*replace` | `replace` sub-option sniff | Matched against `lower(raw_spec)`; `[^)]*` means a nested paren inside `name()` breaks it. Only the literal spelling `replace` (no abbreviation `rep`/`repl`) is recognised, unlike Stata's `REPLACE` convention. | MEDIUM |

Note: the 32-char limit is not derivable from any `c()` macro (Stata has no `c(namelenmax)`), so the
number itself is defensible; the **ASCII-only** character class is the real defect.

### 3f. `layout()` validation — `dash.ado:1221-1231`

```stata
if "`layout'" == "" local layout "auto"
if "`layout'" != "auto" {
    if !regexm("`layout'", "^[1-9][0-9]* [1-9][0-9]*$") &                 ///
       !regexm("`layout'", "^[a-zA-Z_][a-zA-Z0-9_]*:[0-9]+,[0-9]+") &     ///
       !regexm(lower("`layout'"), "^bs") {
```

| problem | file:line | detail | sev |
|---|---|---|---|
| grid form requires exactly **one** space | 1225 | `layout(2  2)` (two spaces), `layout("2 2 ")` with a trailing space, or a tab separator all fail. Stata users routinely get extra whitespace from macro expansion. | MEDIUM |
| `auto` is case-sensitive | 1222 | `layout(Auto)` / `layout(AUTO)` fails, while `bs` at 1227 **is** lowercased first. Inconsistent. | MEDIUM |
| placement form allows `0` | 1226 | `[0-9]+,[0-9]+` accepts `g1:0,0`, but the grid form explicitly rejects zero (`[1-9]`). Inconsistent clamps for the same concept. | MEDIUM |
| placement form is not end-anchored | 1226 | Only the **first** `name:r,c` token is validated; `layout(g1:1,1 @@@garbage@@@)` passes the guard and is handed to Python. | MEDIUM |
| `bs` prefix test is a bare prefix | 1227 | `layout(bsomething)` passes validation (matches `^bs`). | LOW |
| the three forms are three separate hardcoded regexes | 1225-1227 | Adding a layout form means editing both this regex block **and** `dash_render.py:6377-6401`. | LOW |

### 3g. `filterposition()` validation — `dash.ado:1234-1238`

```stata
if "`filterposition'" == "" local filterposition "top"
if "`filterposition'" != "top" & "`filterposition'" != "left" {
    display as error "dash build: filter_position() must be 'top' (default) or 'left' (sidebar)."
```

| problem | detail | sev |
|---|---|---|
| exact-match, case-sensitive | `filterposition(Top)`, `filterposition(LEFT)` fail. Stata option values are conventionally case-insensitive keywords. | MEDIUM |
| no abbreviation | `filterposition(t)` / `(l)` fail. | LOW |
| only 2 values | `right` / `bottom` unsupported (renderer also only handles `top`/`left`, dash_render.py:7367). | LOW |
| **error message names a non-existent option** | says `filter_position()`; the actual option is `filterposition()` (dash.ado:1184). A user who copies the error text gets `r(198) option filter_position() not allowed`. | MEDIUM |

### 3h. Path validator — `dash.ado:150-178` (`_dash_validate_path`)

| rule | file:line | problem | sev |
|---|---|---|---|
| `regexm("`fpath'", "\.\.")` | 154 | Rejects `..` **anywhere in the string**, not just as a path component. Legitimate filenames like `q1..q4_report.html` or a directory `My..Data/` are rejected with a "path traversal" error. Correct check is a component-wise test, or `c(pwd)`-based canonicalisation. | MEDIUM |
| `\.html$` required | 158 | Reasonable, but combined with dash.ado:929 (`if !regexm(...) local saving_path = "`saving_path'.html"`) that line is **dead code** for the explicit-`saving()` branch, since 921 already enforced the suffix, and the tempfile branch at 925 already appends `.html`. | LOW |
| `[;&|<>()]` rejected | 168 | **Parentheses are extremely common in real paths** — `C:\Program Files (x86)\...`, `~/Documents/Report (final)/out.html`. These are rejected outright. `(` and `)` are not shell-dangerous inside a double-quoted argument. | HIGH |
| chars 96, 36, 9, 10, 13 rejected | 172-177 | `` ` `` and `$` guard against Stata macro expansion — correct and necessary. | LOW (good) |
| **not rejected**: `*`, `?`, `[`, `]`, `'`, `"`, `\`, `!`, `#`, `~`, leading `-` | 168-177 | Glob metacharacters and single quotes survive. The value is interpolated into `shell open "`saving_path'"` at 1012-1014 / 1475-1477 inside double quotes, so glob expansion does not occur, but `"` would terminate the quoted argument. `"` is not screened. | MEDIUM |
| no `c(pwd)` / `c(dirsep)` use | throughout | Relative `saving()` paths are never resolved or reported absolutely; the "dashboard saved to X" message (1017, 1474) echoes the relative string. | MEDIUM |
| **server mode bypasses the validator entirely** | 1198-1207 | `dash build, server saving(...)` runs only the `..` check and a `\.py$` check — it **never** calls `_dash_validate_path`, so the shell-metacharacter and backtick/dollar screens do not run on that path. The `.py` path is not shelled out to, but it is written to disk and interpolated into a `python:` line (1466 → `_dash_do_render`), which relies solely on `_dash_json_str` escaping. | MEDIUM |

### 3i. Filter keyword spellings — `dash_parse.mata:892-900`

```mata
if      (i + 5 <= n & substr(lraw, i, 6) == "filter") { matched = 1; klen = 6 }
else if (i + 4 <= n & substr(lraw, i, 5) == "filte")  { matched = 1; klen = 5 }
else if (i + 3 <= n & substr(lraw, i, 4) == "filt")   { matched = 1; klen = 4 }
```

| problem | detail | sev |
|---|---|---|
| exactly three spellings | `filt`, `filte`, `filter`. `fil(...)` (a natural `FILter` minimum abbreviation) is **not** matched, so it survives into `_cmd_nofilter` and `syntax` rejects it: `r(198) option fil() not allowed`. | MEDIUM |
| word-boundary chars | `" "`, `","`, tab, or start-of-string (mata:909). A filter option after a `///` line continuation that collapsed to a newline character would not match. | LOW |
| inconsistent with the graph-level surface | `filter()` at graph level goes through `_expand_optkey` (dash_parse.mata:179-253), which has **no** entry for `filt`/`filte` — so `filt()` works on `dash build` but fails inside a plot spec. Two different hardcoded spellings of the same option. | MEDIUM |
| `filterposition(` false positive — checked, safe | at `filterposition(`, the `"filter"` branch matches but the next non-space char is `p`, not `(`, so it correctly falls through (mata:918-922). Verified by reading the control flow. | — (OK) |

### 3j. Other hardcoded lists

| item | file:line | literal | note | sev |
|---|---|---|---|---|
| Python reserved words in `if_expr` tokenizer | dash_parse.mata:731-732 | `True False None nan NaN inf and or not in is` | Missing `if`, `else`, `lambda`, `for`, `abs`, `min`, `max`, `len`. Harmless — dash.ado:1310-1312/1535-1537 filters with `capture confirm variable`. | LOW |
| operator strip list in `if_expr` | dash_parse.mata:821-839 | 18 hardcoded `subinstr` calls | Missing `^`, `:`, `[`, `]`, `{`, `}`, `=` (single), `@`. A `varname[_n-1]` style expression leaves `_n` as a token (filtered later). | LOW |
| JSON var-extraction key list | dash_parse.mata:667-671 | `yvar xvar var yvar1 yvar2 y1var x1var y2var x2var mlabel colorvar` | **`jitter`/`jseed` are fine, but no key for `weight`** (dash has no weight support) and none for `base`. Complete for the current schema. | LOW |
| `dash serve` port clamp | dash.ado:1498 | `< 1024 | > 65535` | Reasonable. Note the message at 1499 says "between 1024 and 65535" and matches. | LOW |
| `dash_setup` package list + min versions | dash_setup.ado:66-71 | `bokeh 3.0`, `numpy 1.23`, `scipy 1.9`, `statsmodels 0.13`, `pandas 1.5` | Duplicated as prose in `dash.pkg:13-14`; two hardcodings to keep in sync. | LOW |
| `dash_setup` uses `pip install` unpinned | dash_setup.ado:81, 45 | installs latest | No upper bound; a future breaking bokeh 4 would be installed silently. | MEDIUM |
| `version 16.0` | dash.ado:59 and every `program define`; dash_setup.ado:15 | fixed | Correct practice (version control of interpretation); should **not** track `c(stata_version)`. | LOW (good) |

---

## 4. The option-abbreviation table is itself the hardcoding problem

### The mechanism

Stata's `syntax` derives minimum abbreviations from capitalisation in the option declaration
(`TItle(string)` ⇒ `ti`, `tit`, `titl`, `title` all accepted). `dash` instead declares **every**
graph/plot option in all-lowercase (`dash.ado:230-246` for graph level, `293-326` for plot level),
which means `syntax` requires the exact full name, and then simulates abbreviation with a fixed
lookup chain in Mata (`dash_parse.mata:179-253`, `_expand_optkey`). Unrecognised keys pass through
**unchanged** (`dash_parse.mata:252 — return(name)`), so the failure surfaces at the `syntax` call as
`r(198) option <key>() not allowed`.

The structural defect: **the table maps exactly one short form per option**, whereas Stata accepts
*every* prefix from the minimum abbreviation up to the full name.

Note `dash_setup.ado` / `_dash_build` / `_dash_kpi` **do** use proper capitalised declarations
(`SAVing`, `TItle`, `SUBtitle`, `LAYout`, `THEME`, `FILTERPOSition`, `PORT`, `FMT`, `COLOR`,
`UPDATE` at dash.ado:1063-1071, 1174-1185, 1488) — so the two halves of the command behave
differently. That inconsistency is itself worth fixing.

### Enumerated failures (each is `r(198) option X() not allowed` from `_dash_parse_plot_opts` / `_dash_parse_graph_opts`)

| user types | Stata twoway meaning | dash table (mata:line) | result in dash | sev |
|---|---|---|---|---|
| `mlab(make)` | `mlab:el` — **the documented Stata minimum** | table has only `mla` (185) | `r(198) option mlab() not allowed` | HIGH |
| `mlabe(make)`, `mlabel(make)` | mlabel | `mlabel` full name is in `syntax` (297) | `mlabel()` works; `mlabe()` fails | HIGH |
| `msym(oh)`, `msy(oh)`, `msymb`, `msymbo` | `msy:mbol` | table has only `ms` (182) | all four fail | HIGH |
| `xlab(0(10)50)` | `xlab:el` — **and `dash.sthlp:639` documents `{cmdab:xlab:el}`** | table has only `xla` (212) | `r(198) option xlab() not allowed` — **dash's own help file documents a spelling that does not work**; line 637 of the same help documents `{cmdab:xla:bel}`. The help contradicts itself. | HIGH |
| `ylab(...)`, `ylabe(...)` | `ylab:el` | only `yla` (213) | fail; same self-contradiction at dash.sthlp:638 | HIGH |
| `xtit("X")`, `xtitl("X")` | `xtit:le` | only `xti` (210) | fail | HIGH |
| `ytit("Y")`, `ytitl("Y")` | `ytit:le` | only `yti` (211) | fail | HIGH |
| `lcol(red)`, `lco`, `lcolo` | `lc:olor` | only `lc` (202) | fail | HIGH |
| `lwid(thick)`, `lwi`, `lwidt` | `lw:idth` | only `lw` (203) | fail | HIGH |
| `lpat(dash)`, `lpa`, `lpatt`, `lpatte`, `lpatter` | `lp:attern` | only `lp` (204) | fail | HIGH |
| `mcol(navy)`, `mco`, `mcolo` | `mc:olor` | only `mc` (181) | fail | HIGH |
| `msiz(large)` | `msi:ze` | only `msi` (183) | fail | HIGH |
| `lege(off)`, `legen(off)` | `leg:end` | only `leg` (216) | fail | HIGH |
| `subt("S")`, `subti`, `subtit`, `subtitl` | `sub:title` | only `sub` (209) | fail | HIGH |
| `capt("C")`, `capti`, `captio` | `cap:tion` | only `cap` (215) | fail | HIGH |
| `no("n")`, `not("n")` | `no:te` | only the full `note` (214) | fail | HIGH |
| `tit("T")`, `titl("T")` | `ti:tle` | only `ti` (208) | fail | HIGH |
| `savi(f.html)`, `savin` | `sav:ing` | only `sav` (217) | fail | MEDIUM |
| `name`/`na`/`nam` | `nam:e` | `nam` (218) + `name` passthrough; `na` fails | mostly OK | LOW |
| `aspe(1)`, `aspec`, `aspect`, `aspectr`… | `asp:ectratio` | only `asp` (224) | fail | MEDIUM |
| `xsca`, `xscal` | `xsc:ale` | only `xsc` (220) | fail | MEDIUM |
| `xlin(0)`, `xli(0)` | `xli:ne` | only `xl` (222) — **note `xl` is shorter than Stata's own minimum `xli`, and `xli` itself fails** | fail | HIGH |
| `yli(0)`, `ylin(0)` | `yli:ne` | only `yl` (223); `yli` fails | fail | HIGH |
| `fint(50)`, `finte`, `fintens`… | `fi:ntensity` | only `fi` (196) | fail | MEDIUM |
| `fcol(blue)`, `fco` | `fc:olor` | only `fc` (195) | fail | MEDIUM |
| `bwi(0.5)`, `bwid`… | `bw:idth` for bar width vs. `bwidth()` for lowess | dash has **both** `bw`→`barwidth` (200) and `bwid`→`bwidth` (249) — a deliberate but undocumented collision. `bwi` fails. | MEDIUM |

### Semantic mis-mappings (worse than a plain failure — these silently do the wrong thing)

| user types | Stata meaning | dash expands to (mata:line) | consequence | sev |
|---|---|---|---|---|
| `mlc(red)` | **`mlc:olor`** = marker *line* (outline) colour | `mlabcolor` (186) | The marker-label colour is set instead of the marker outline. `mlcolor()` *is* declared in `syntax` (dash.ado:297), so the full name works — but the standard Stata abbreviation is hijacked. **Silent wrong output, no error.** | HIGH |
| `mlw(thick)` | **`mlw:idth`** = marker line width | `mlabwidth` (190) | `mlwidth` is not in `_dash_parse_plot_opts` at all (dash.ado:293-326) — there is **no** way to set marker outline width. `mlw()` silently sets a label width instead. | HIGH |
| `mls(small)` | `mls:tyle` = marker style | `mlabsize` (187) | Silently sets label size. | MEDIUM |
| `mlp(3)` | `mlabp:osition` (Stata's minimum is `mlabp`, not `mlp`) | `mlabposition` (188) | Works by accident; `mlabp(3)` — the *real* Stata spelling — **fails**. `dash.sthlp:540` documents `{cmdab:mlap:osition}`, which also fails. | HIGH |
| `mlg(2)` | `mlabg:ap` | `mlabgap` (189) | Same pattern; `mlabg(2)` fails; help documents `mlag` (dash.sthlp:543), which also fails. | HIGH |
| `m(circle)` | in Stata, `m()` is not a twoway option (`msymbol` min is `msy`) | `marker` (193) | dash invents a `marker()` option that Stata does not have. | MEDIUM |

### The help file documents abbreviations the table does not implement (verified)

`grep -o '{cmdab:[a-z]*:[a-z]*' dash.sthlp` vs. `_expand_optkey`:

| documented in dash.sthlp | line | in the Mata table? | result |
|---|---|---|---|
| `mla:bel` | 533 | yes (`mla`) | OK |
| `mlac:olor` | 537 | **no** | `r(198) option mlac() not allowed` |
| `mlas:ize` | 538 | **no** | `r(198)` |
| `mlap:osition` | 540 | **no** | `r(198)` |
| `mlag:ap` | 543 | **no** | `r(198)` |
| `xla:bel` | 637 | yes (`xla`) | OK |
| `yla:bel` | 638 | yes (`yla`) | OK |
| `xlab:el` | **639** | **no** | `r(198)` — same help file, contradicts line 637 |
| `ti:tle`, `sub:title`, `no:te`, `cap:tion`, `leg:end`, `sav:ing`, `nam:e`, `sch:eme`, `asp:ectratio`, `xti:tle`, `yti:tle`, `xsc:ale`, `ysc:ale`, `xli:ne`, `yli:ne` | various | only the exact 2-3 char key is present; **the documented minimum means every longer prefix should also work, and none do** | partial |
| `lay:out`, `fmt:`, `upd:ate` | 247, 381, 394 | n/a — these go through real capitalised `syntax` declarations (`LAYout`, `FMT`, `UPDATE`) | OK |

**No test covers this.** `test/test_parser.cscript:58-78,161-189` and `test/test_tokenizer.cscript:130-144`
exercise only `mc`, `ms`, `fc`, `fa`, `title`, `name`, `saving`. No cscript tests any abbreviation
that the table lacks, so the whole class of failures is untested.

### The fix (for the implementation plan)

Delete `_expand_optkey` and capitalise the declarations in `_dash_parse_graph_opts`
(dash.ado:230-246) and `_dash_parse_plot_opts` (dash.ado:293-326) to match Stata's own minimums —
`MColor()`, `MSYmbol()`, `MSIze()`, `MLABel()`, `MLABColor()`, `MLABSize()`, `MLABPosition()`,
`MLABGap()`, `MLColor()`, `MLWidth()`, `LColor()`, `LWidth()`, `LPattern()`, `FColor()`,
`FIntensity()`, `TItle()`, `SUBtitle()`, `NOte()`, `CAPtion()`, `LEGend()`, `XTItle()`, `YTItle()`,
`XLABel()`, `YLABel()`, `XLIne()`, `YLIne()`, `XSCale()`, `YSCale()`, `ASPectratio()`, `SAVing()`,
`NAMe()`, `SCHeme()`, `FILter()`. That makes the abbreviation surface identical to Stata's by
construction and removes 75 lines of hand-maintained table. `_dash_expand_opts_str`
(dash_parse.mata:269-391) would still be needed for nothing — it can be reduced to a pass-through or
deleted once `_expand_optkey` is gone.

---

## 5. Environment / `c()` state that is never consulted

`grep -n 'c(' dash.ado` returns **11 hits, all of them from just two idioms**:

```
dash.ado:998, 1457, 1623 :  local render_py "`c(sysdir_plus)'d/dash_render.py"   (last-resort fallback)
dash.ado:1012-1014, 1475-1477 : if "`c(os)'" == "MacOSX" / "Windows" / "Unix"    (browser open)
```

`grep` for `c(` in `dash_parse.mata` and `dash_setup.ado`: **zero hits.**
`grep` for `creturn`, `set scheme`, `graph set`: **zero hits in all three files.**

| `c()` / state | consulted? | should be | consequence | sev |
|---|---|---|---|---|
| **`c(scheme)`** / current `set scheme` | **NO** | default for `theme()` in `dash build` (dash.ado:1282) and for the immediate/serve paths (974, 1603) | **A user with `set scheme economist` in `profile.do` gets s2color from `dash`, always.** `dash_render.py:1142` and `:5000` both hardwire `"s2color"` as the terminal fallback. `dash` bundles approximations of exactly the 5 schemes at `schemes/` — `s2color`, `s1color`, `s1mono`, `economist`, `sj` — and `dash_render.py:704-706` hardcodes that same 5-name set as `_BUILTIN_NAMES`, independently of what is on disk. | HIGH |
| **`c(level)`** / `set level` | **NO** | the CI level for `lfitci`, `qfitci`, `lpolyci`, `fpfitci` | `dash_render.py:2441`, `8101`, `8123` hardcode `scipy_stats.t.ppf(0.975, ...)` — **always 95%**. There is no `level()` option anywhere in `dash.ado` (`grep -in level dash.ado` → 0 hits) and none in `dash.sthlp`. A user with `set level 90` gets a 95% band with no warning. Stata's `twoway lfitci` honours both `level()` and `c(level)`. | HIGH |
| **display formats** (`: format varname`) | **NO** | axis/hover/KPI formatting — see §2 | see §2d | HIGH |
| **`c(pwd)`** | **NO** | resolving/echoing relative `saving()` paths; the scheme-file CWD search in `dash_render.py:751` uses Python's `os.getcwd()`, which is **not guaranteed to equal Stata's `c(pwd)`** when Stata's embedded Python was started from a different directory | `scheme(mycustom.scheme)` may resolve against the wrong directory. Also the "saved to X" messages (dash.ado:1017, 1474) echo an unresolved relative path. | MEDIUM |
| **`c(os)`** | partially — only for browser-opening | also for `c(dirsep)` in path handling, and for choosing the `xdg-open` fallback chain | The three-way `c(os)` test at 1012-1014/1475-1477 is correct, but no `open`/`xdg-open` availability check; on a headless Linux box `xdg-open` may not exist and the `shell` fails silently (no `_rc` check after any of the six `shell` lines). | MEDIUM |
| **`c(stata_version)`** | **NO** | — | Correct: `version 16.0` pins interpretation and should not be dynamic. | LOW (good) |
| **`c(maxvar)`**, `c(max_N_theory)`, `c(memory)` | **NO** | a guard before serialising the whole dataset to JSON (§2e) | No size check before base64-embedding the data into the HTML. | MEDIUM |
| **`c(current_date)` / `c(current_time)`** | **NO** | provenance stamp in the generated HTML | Cosmetic. | LOW |
| **`c(filename)` / `c(frame)`** | **NO** | `dataSource` provenance (jsonio already emits a `dataSource` field via `c(filename)` internally, jsonio.ado:199) | Already handled by jsonio. | LOW |
| **`c(dirsep)`** | **NO** | `_dash_validate_path` and the `findfile`-derived `substr(...)` path arithmetic at dash.ado:48-49, 994-995, 1453-1454, 1619-1620 | The `substr(fn, 1, strlen(fn) - strlen("dash.ado"))` idiom is separator-agnostic, so this is fine in practice. | LOW |
| **`c(rmsg)` / `set trace`** | **NO** | — | n/a | LOW |

### 5b. Packaging defect discovered while checking scheme resolution (HIGH)

`dash.pkg:20-25` ships exactly six files:

```
f dash.ado
f dash.sthlp
f dash_setup.ado
f dash_setup.sthlp
f dash_parse.mata
f dash_render.py
```

**`schemes/*.scheme` is not shipped.** `dash_render.py:702` computes
`_SCHEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schemes")` — i.e. it looks
for a `schemes/` directory next to the installed `dash_render.py` (which would be `PLUS/d/schemes/`).
After `net install dash`, that directory does not exist. `SchemeParser._resolve_path`
(dash_render.py:762-801) then raises `ValueError`, and while `DashRenderer.__init__`
(dash_render.py:5002-5005) catches that with

```python
except (ValueError, OSError):
    self.scheme = SchemeParser("s2color")
```

the **fallback raises the identical `ValueError`** because `s2color.scheme` is equally missing — and
that second exception is uncaught. **Every `dash` invocation from a packaged install would traceback.**
Fix: add `f schemes/s2color.scheme` … (5 lines) to `dash.pkg`, and/or make `SchemeParser` degrade to a
built-in dict of defaults.

Also: `stata.toc` (3 lines) has no version/date line; `dash.pkg:18` says `Version: 1.0.0 25mar2026`
while `dash.ado:1` says `v2.0` and `dash.ado:21` says `Version: 2.0 27mar2026`, and
`dash_parse.mata:1` says `v2.0`. Three inconsistent hardcoded version strings. LOW.

---

## 6. Browser-opening and shell-out behaviour

### Every shell-out in `dash.ado`

| file:line | code | guarded by | sev |
|---|---|---|---|
| dash.ado:1012 | `if "`c(os)'" == "MacOSX"  shell open        "`saving_path'"` | `if "`open_browser'" == "1"` (1008) — true **only** when `saving()` was omitted (1927) | — |
| dash.ado:1013 | `if "`c(os)'" == "Windows" shell start "" "`saving_path'"` | same | — |
| dash.ado:1014 | `if "`c(os)'" == "Unix"    shell xdg-open "`saving_path'"` | same | — |
| dash.ado:1475 | `if "`c(os)'" == "MacOSX"  shell open        "`saving'"` | `else` branch of `if "`server'" != ""` (1473) — i.e. **unconditional for every non-server `dash build`** | HIGH |
| dash.ado:1476 | `if "`c(os)'" == "Windows" shell start "" "`saving'"` | same | HIGH |
| dash.ado:1477 | `if "`c(os)'" == "Unix"    shell xdg-open "`saving'"` | same | HIGH |

(`dash serve` does not `shell` — it passes `--no-browser` into `sys.argv` for the Python renderer,
dash.ado:1627-1628, 1645-1647.)

### The option surface

| command | `syntax` line | has `nobrowser`? |
|---|---|---|
| `dash <plotspec>` | dash.ado:230-246 / 293-326 | **NO** |
| `dash build` | **dash.ado:1174-1185** — `SAVing TItle SUBtitle LAYout LINK THEME REPLACE SERVER TABS FILTERPOSition` | **NO** |
| `dash serve` | dash.ado:1488 — `[, PORT(string) NOBROWSER TIMEOUT(string)]` | **YES** |
| `dash kpi` | dash.ado:1063-1071 | n/a |
| `dash clear` | dash.ado:1025 (no args) | n/a |

**Findings:**

| finding | detail | sev |
|---|---|---|
| **`dash build` always opens a browser** | dash.ado:1473-1478 has no opt-out. Every `dash build, saving(out.html) replace` in a batch script, a `cscript`, a cron job, a CI run, or a Stata session over SSH spawns a browser (or, on a headless box, fails). `dash serve` — the *interactive* subcommand — is the only one with `nobrowser`. | HIGH |
| **immediate `dash` opens a browser whenever `saving()` is omitted** | dash.ado:926-927 sets `open_browser = 1`. No opt-out; the only way to suppress it is to supply `saving()`, which also changes where the file goes. | HIGH |
| `dash.sthlp` documents `nobrowser` only for `serve` | dash.sthlp:96, 215, 251 | — (consistent with code) |
| **no `_rc` check after any `shell`** | all six lines | A failed `xdg-open` (common on headless Linux / WSL / containers) is completely silent; the user sees "dashboard saved to …" or, in the immediate path, nothing at all (the `display` at 1017 is in the `else` branch, so the browser path prints **no** message telling the user where the file is). | MEDIUM |
| **immediate path never tells the user the path** | dash.ado:1008-1018 — the `display as text "dash: dashboard saved to …"` is only in the `else`. When a browser is opened, the tempfile path is never shown, so if the browser fails the output is unreachable. | MEDIUM |
| `shell start "" "path"` Windows fix | dash.ado:1013, 1476 — correct (empty title argument). | LOW (good) |
| the path reaching `shell` is screened | `_dash_validate_path` (150-178) runs for explicit `saving()` in the immediate path (921) and non-server `dash build` (1209). The tempfile path (924) is Stata-generated. | LOW (good) |

**Recommended surface:** add `NOBROwser` to `_dash_build`'s `syntax` (dash.ado:1174) and to the plot-level
option set; add a `BROwser`/`NOBROwser` pair or honour a `global dash_nobrowser`; check `_rc` after
each `shell` and fall back to `display as text` with the absolute path; always display the path.

---

## Consolidated priority list

1. **§1c — `dash serve` ignores every build option** (layout, link, filter, theme, title, subtitle, tabs, filter_position all literal). Six HIGH items in one line, `dash.ado:1603`.
2. **§1a/§5 — `scheme()` is parsed, escaped, stored and then never read.** `dash.ado:974` + `dash_render.py:4990-5000`. Plus `c(scheme)` never consulted anywhere.
3. **§4 — the abbreviation table.** ~25 standard twoway abbreviations hard-fail with `r(198)`, and 5 (`mlc`, `mlw`, `mls`, `mlp`, `mlg`) are mis-mapped to *different options* — silent wrong output. `dash.sthlp` documents 5 spellings (`mlac`, `mlas`, `mlap`, `mlag`, `xlab`) that do not work. Zero test coverage.
4. **§2 — display formats.** `metaprint()` is a verified no-op (jsonio.ado:238), and jsonio as shipped **cannot** emit formats through any option, so this needs a Stata-side side-channel. Every `%td`/`%tc` date is a raw number in the browser.
5. **§5b — `dash.pkg` does not ship `schemes/`**, which makes a packaged install traceback on the first render (the `except` fallback re-raises).
6. **§6 — `dash build` has no `nobrowser`**, and no `shell` return code is ever checked.
7. **§5 — `c(level)` / no `level()` option**; CI bands hardcoded at `0.975` in three places.
8. **§3d — KPI default display value ignores the variable's own `format`.**
9. **§3h — path validator rejects `(`/`)`** (breaks `Program Files (x86)` and any parenthesised folder) and treats any `..` substring as traversal; server-mode `saving()` bypasses the validator entirely.
10. **§3e — ASCII-only name regexes** reject Stata 14+ Unicode variable names; the `filter()` one (dash.ado:1351) drops them **silently**.
