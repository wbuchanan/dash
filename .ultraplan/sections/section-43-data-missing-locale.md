# Section 43: Extended missing values, locale and the data path

> Part of: WP-31 · GAPS3 rows: G1, G2, G3, G4, G5 · Risk: yellow · Batch: 14 · Depends on: 01 · Blocks: -- · Tasks: 4, 5 commits · Case-id prefix: U43

## Overview

**What is wrong today.** GAPS3 G1 (GAPS3.md:226): "Extended missing `.a`-`.z` merged into one null in by(, missing) panels, marker labels, filters, tooltips." G2 (:227): "`set dp comma` never read; `%tC` converted without leap seconds (up to 27 s); `graph set` font faces not read." G3 (:228): "Working columns are generated in the user's data (r(900) possible at `c(maxvar)`); user variables named `x`, `y`, `top`, `count`, `density` shadowed in `hover()`/`mlabel()`; numbers embedded as JSON text (~0.5 GB per million values); strL check loops per observation; a faceted computed-only graph counted in full; `$dash_max_cells` counts every exported row." G4 (:229): "Carried columns (`hover()`, `mlabel`, row id) upcast to dtype=object and handed to Bokeh as Python lists; bokeh 3.8 validates item by item (7.5 of 7.7 s on a million-row line)." G5 (:230): "One ~33 KB format-writer model per distinct tick format and per (fmt, kind) tooltip."

At `6370ca4`: the data writer `_dash_write_stata_data` (dash_render.py:2419ff) writes "Every missing value, . and .a to .z, as None: jsonio's `null`" (:2495-2497), though `_dash_label_key` (:2396-2415) already knows jsonio's code for an extended missing value's LABEL; dash_parse.mata:2160 writes `.a-.z` as `null` in `_dash_json_number17`; the help (dash.sthlp:2888-2890) says dash "cannot" draw them "because the data it is handed carry every missing value alike". `c(dp)` appears nowhere (`grep -c 'c(dp)' dash.ado dash_render.py` = 0); `_dash_fmt_parse`'s grammar (:26933-26934) reads `[.,]` from the FORMAT only. `%tC` is converted with `%tc`'s epoch and a warning (:652-660). `_DASH_GT_FONTS` (:33988-33992) is three fixed CSS families ("a `graph set` font is not read; P2.22"). `_carry_cols` (:12387-12423) does `np.asarray(_v, dtype=object)` then `.tolist()` for every carried column and skips any key already in `data` (so a user variable named `x`, `y`, `top`, `count` or `density` is dropped from hover). `_dash_fmt_tick_formatter` caches one `CustomJSTickFormatter` per `(fmt, kind, storage)` per document (:27938-27952), each carrying `_DASH_FMT_JS` (about 33 KB) in `code`.

**After this section**, both modes: an extended missing value keeps its letter -- a `by(, missing)` panel is titled `.a`/its value label, a marker label and a tooltip show `.a`, a dropdown filter offers `.a` as its own choice; `set dp comma` is honoured by every number writer (Python and the JS twin, ticks, tooltips, marker labels, KPI cards); `%tC` is converted with Stata's own leap-second table (measured from `Cofc()`); the three `{stSans}`/`{stSerif}`/`{stMono}` families follow `graph set` where the probe shows where Stata keeps them; a hover()/mlabel variable named like a derived key is carried under a reserved alias and read from it; numeric carried columns stay arrays; the `_dash_cell_cap` count is the planned embedding; one writer model exists per distinct `(fmt, kind, storage, how, dp)` per page and the help documents the cost with the measured size. Two G3 parts (a binary data file, the strL per-observation loop) are filed as residuals (D-43d).

**Why these rows share a section.** All five are the data path from dash.ado's writer through the loader to the format writers and the carried columns -- the "loader/export/missing" owner of batch 14 (index). S42 (graph text) and S41 (colours) do not touch these functions.

**Test order and commit rule.** Five cycles, one commit per row, in the order G4 (arrays; smallest, and G1's new columns ride on it), G1, G2, G3, G5. 43-01 writes the extractor and every red test (no commit); 43-02 commits G4 and G1; 43-03 commits G2; 43-04 commits G3 and G5 and hands back.

### Section decisions (binding on the executor)

- **D-43a. Extended missing values travel as a parallel code column.** The data file keeps jsonio's layout (a missing number is `"null"`) and gains one key, `extendedMissing`: `{"<var>": {"<row index>": "a", ...}}`, present only for variables that hold any `.a`-`.z` (sfi's `Missing` objects, as `_dash_label_key` reads them). The loader (`_dash_load_columns` region, :701ff) builds for each such variable a text column `__dashm_<var>` holding `""` or `.a`..`.z`, attached to the frame, and the renderer carries it beside the variable wherever the variable is carried (`_carry_cols` carries every column, so it rides along). Sinks: `_dash_by_groups` (:4361) keys a panel by `(value, code)` so `.a` and `.b` are two panels titled by `_dash_fmt_text` of the code or the value label (jsonio key `_DASH_MISSING_LABEL_KEY + k`); the mlabel writer passes the code; the hover formatter JS (`dash_fmt_text`) takes the code as a sixth argument read from `@{__dashm_<var>}`; `_build_filter_widgets`'s dropdown categories list each code as its own option after `"(missing)"` is renamed to the code where the variable has codes. The reserved prefix `__dash` is dash.ado's (dash.ado:6555-6559 refuses user variables named with it).
- **D-43b. `set dp comma` is a page-level setting.** dash.ado writes `"dp": "`c(dp)'"` into the spec's `build_options` (`_dash_plot`'s JSON at :7451 region; the key list of seven does NOT change -- `dp` is a build option, written once beside `level`). `_dash_fmt(value, fmt, storage=None, strip=False, dp="period")`: when `dp == "comma"` and the parsed numeric format's separator is `.`, the separator becomes `,` (Stata: `set dp comma` makes `%9.2f` print `3,14`; the thousands separator of `%9.2fc` becomes `.`); a date picture is unchanged. The JS twin `dash_fmt(value, fmt, storage, strip, dp)` mirrors it; `_dash_fmt_model_args` adds `dp` to every writer's args; the renderer reads `spec["build_options"].get("dp", "period")` once into `self.dp` and every `_dash_fmt`/writer call passes it. U43-03 measures `display %9.2f 3.14159` and `display %9.2fc 1234.5` under `set dp comma`.
- **D-43c. The leap-second table is Stata's own, measured.** `_STATA_LEAP_SECONDS_TC_MS: tuple` holds the 27 `%tc` instants (ms) after which one second is added, written by the probe from `Cofc()`: for each candidate date d in the IERS list (30jun1972, 31dec1972, 31dec1973, ..., 31dec2016) the probe records `Cofc(tc(d 23:59:59.999)+1) - (tc(d 23:59:59.999)+1)`; the table is the set of instants where that difference steps by 1000. `_dash_tc_from_tC(values)`: for each `%tC` value v, `v - 1000 * (number of table instants t with t + 1000*index(t) <= v)` -- the inverse of `Cofc`, bounded by a 27-step scan (`np.searchsorted` over the cumulative table). The warning at :654-660 is removed; the help's `%tC` sentence changes to "converted with Stata's leap-second table". The JS twin for date tick formatting (`dash_fmt_date` in `_DASH_FMT_JS`) receives `%tC` values already converted (the axis holds `%tc` ms), so no JS table is needed; tooltips of a `%tC` variable format the stored `%tC` number with `cofC` applied in Python before embedding (the hover source column), pinned by `TestLeapSeconds::test_tooltip_is_statas`.
- **D-43d. G3 is closed in two parts and two residuals.** Closed: (i) derived-key shadowing -- `_carry_cols` carries a column whose key is already in `data` under `__dashu_<name>`, and `GlyphMapper._user_field(name, data)` returns `__dashu_<name>` when present else `name`; `_hover_tool` (:12425ff) and `_apply_mlabel_opts` (:14104) look fields up through it; (ii) the cell count -- `_dash_cell_cap` (dash.ado:4276ff) is handed the planned count (rows x variables that WILL be embedded: the primary frame's columns, per graph the union of plotted, hover(), mlabel, by and filter variables, computed-only graphs' rows excluded), measured by U43-06 against `c(maxvar)`-sized data. Residuals, filed as open BUGS.md entries `G3b` and `G3c` with GAPS3 `G3 Tracked: Partly closed`: a binary/base64 data file (changes the file format both renderers and the served route read; L), and the strL per-observation loop (dash.ado:4262 region; needs a Mata `st_sview` pass; S). Listed for ratification.
- **D-43e. G5 is closed by one model per distinct quadruple and the documented cost.** Bokeh has no way to share a formatter's `code` across models without a page script, and a page without filters has no callback to carry one; the per-model code is the price. Closed form: the cache key becomes `(how, fmt, kind, storage, dp)` for ticks AND tooltips (`CustomJSHover` writers join the same per-document cache), `test_one_writer_per_quadruple` pins that no page holds two writers with equal keys, `test_writer_size_is_documented` pins the help's number (bytes of `_DASH_FMT_JS`, rounded to the KB) -- M17's "document with a measured example". Listed for ratification.
- **D-43f. `graph set` fonts follow U43-04.** The probe sets `graph set svg fontface Courier`, `graph set window fontface Courier`, then captures `graph set` and `graph query`'s output and `macro list`/`char list` to find where Stata keeps the value. If a readable home exists (a global, a `c()` value or `graph set <device> fontface` printing it), dash.ado reads it at registration into `build_options["fontface"]` (and `fontfacesans`, `fontfaceserif`, `fontfacemono` when `graph set` offers them) and the renderer feeds `_DASH_GT_FONTS` through a per-render dict `self.gt_fonts` (defaults the three families; a set face is prepended: `"Courier, Helvetica, Arial, sans-serif"`). If no readable home exists, G2's font part is a documented limit with the probe's output quoted in the help (M17).
- **D-43g. G4: numeric carried columns stay arrays.** In `_carry_cols`, `_col = np.asarray(_v)`; if `_col.dtype.kind in "fiub"` keep it as a float64 array (`astype(float)` for ints so NaN can stand for a dropped row) after the selector; else fall back to the object list. Datetime columns stay arrays (the :43028-43034 rule). `_snapshot_of`/`_to_serialisable` already serialise arrays.

## Risk: [yellow] -- the data file gains a key, every number writer gains an argument, and the carried-column type changes

**Why.** `_dash_fmt` has many callers (ticks, tooltips, mlabel, KPI, CSV); the JS twin's signature changes; a new data-file key must be ignored by old readers and read by both renderers; `_carry_cols` feeds every derived source.

**Risk factors.** 1. A `_dash_fmt` caller left without `dp` prints a period under `set dp comma` (silent). 2. The served route reads the data file through its own loader path (`_dash_load_columns` is shared; the served `make_document` reads the same JSON): the new key must survive the base64 embedding. 3. A carried float array where a list was expected (tests comparing `== [..]`). 4. `by(, missing)` panel count changes for data with several codes (pinned in test_by*.py). 5. The dropdown's `"(missing)"` option is S49's (batch 16, H2f) -- S43 adds code options only; S49 later adds the `"(missing)"` toggle and must read `__dashm_*`.

**Mitigation.** 1. `TestDpComma::test_every_fmt_caller_passes_dp` scans dash_render.py for `_dash_fmt(` and `_dash_fmt_text(` calls and asserts each passes `dp=` or `self.dp`. 2. `TestExtendedMissing::test_served_reads_the_codes`. 3. 43-01's simulated-fix red list. 4. Flipped with the reason. 5. Notes for S49.

## Dependencies

- **Depends on: 01.** Blocks none (S49 reads what S43 leaves).
- **Parallel batch: 14**, merge order S41, S42, S43. **Can run with S41 and S42**: S43 edits `_dash_write_stata_data`, `_dash_load_columns`, `_dash_by_groups`, `_carry_cols`, `_hover_tool`, `_apply_mlabel_opts` (field lookup only), the format writers (:26925-28020), `_DASH_FMT_JS`, `_DASH_GT_FONTS`'s reader, dash.ado's data writer and `_dash_cell_cap`; S41 and S42 touch none of these. Both S42 and S43 append classes to test_graph_text.py (S42's `TestOtherSmcl*`, S43's `TestGraphSetFonts`), at the end, merge order S42 then S43.

## Evidence

### G1

```python
2495            # Every missing value, . and .a to .z, as None: jsonio's "null".
2496            cols[v] = ["null" if x is None else float(x)
2497                       for x in _column(v, missingval=None)]
2396 def _dash_label_key(value):
2397     """The key a value label is written under: the integer as text, and an
2398     extended missing value (``".a"``, as sfi names it) as jsonio's code."""
```
`_dash_by_groups(work_df, by_vars, by_missing, limit, where="")` (:4361) and `_dash_by_value_missing` (:4384); `(missing)` panel title rule at :4328-4329. Marker labels: `_apply_mlabel_opts` (:14104; label column kinds at :14682 `(is_text, missing)`). Tooltips: `_hover_tool` (:12425) and the `CustomJSHover` writers (`_dash_fmt_model_args` :27900 region). Filters: `_build_filter_widgets` (:45427) dropdown categories (`"(missing)"` at :13676, :13999 for colorvar legends). dash.sthlp:2888-2890 states the limit.

### G2

`_DASH_FMT_NUM_RE` (:26933-26934) `^%(-)?(0)?(\d{1,4})([.,])(\d{1,4})(f|g|e)(c)?$`; `_dash_fmt` (:27859-27908); `_dash_fmt_text` (:27909); JS `dash_fmt` (:24309-24340) and `dash_fmt_text` (:24340-24344); the JS regex twin at :23396. `%tC`: :531-534 (range comment), :652-660 (the warning). Fonts: :33988-33992.

### G3, G4

```python
12416        for _k, _v in dict(getattr(source, "data", {}) or {}).items():
12417            if _k in data:
12418                continue
12419            try:
12420                _col = np.asarray(_v, dtype=object)
12421                if selector is not None:
12422                    _col = _col[selector]
12423                if len(_col) != _n:
12424                    continue
12425                data[_k] = _col.tolist()
```
dash.ado:6555-6559 (the `__dash` prefix refusal and its list of reserved columns: `__dashq#`, `__dashs#`, `__dasht#`, `__dash_row__`, marker-label and jitter columns); `_dash_cell_cap` (:4276, comment :4262-4275 explains `<nvars>`, `<extra>`, `<served>`); :1772-1792 (`_LARGE_DATASET_CELLS`, `_HTML_BYTES_PER_CELL`); :43028-43034 (date columns stay arrays).

### G5

```python
27945    key = ("tick", args["fmt"], args["kind"], args["storage"])
27946    if cache is not None and key in cache:
27947        return cache[key]
27948    model = CustomJSTickFormatter(
27949        args=args, code=_DASH_FMT_JS + _DASH_FMT_MODEL_JS % (("tick",) * 3))
```
`len(_DASH_FMT_JS)` is measured by 43-01 and written into the help.

### Stata's rules

`help set dp`: `set dp comma` makes a period in output a comma and vice versa for the thousands separator; `c(dp)` is `period` or `comma`. `help datetime`: `%tC` counts leap seconds; `Cofc()`/`cofC()` convert; 27 leap seconds through 2016. `help graph set`: `graph set <device> fontface <name>` and `fontfacesans|serif|mono` (whether the value is readable from a program: U43-04). Extended missing: `help missing`; `by(, missing)` draws a panel per missing value (twoway `by()` with `missing`: measured by U43-02 -- one panel per code or one `(missing)`? the probe decides the title and count).

### Tests pinning today's behaviour

test_by*.py nodes counting panels under `by(v, missing)` with several codes; test_display_format_writer.py::TestJavaScriptTwin (signature of `dash_fmt`), ::TestPythonWriter (period under any dp); test_marker_label_parity.py and test_string_value_export.py nodes asserting `.a` renders as `.`; test_dates.py `%tC` warning node (`pytest.warns`); test_hover*.py nodes asserting a user `x` variable is absent from hover; test nodes comparing carried columns with lists (`== [...]`); test_function_audit.py may reach `_carry_cols`.

## User stories

- US-43.1 As a Stata user with `.a`/`.b` codes, I want panels, labels, tooltips and filters to show the code or its label, as twoway does.
- US-43.2 As a user who `set dp comma`, I want every number dash writes to use my decimal mark.
- US-43.3 As a user of `%tC`, I want the timestamps right to the second.
- US-43.4 As a user whose variable is named `x` or `count`, I want `hover(x)` to show it.
- US-43.5 As a user of a million rows, I want the page built without a 7-second list validation.
- US-43.6 As a maintainer, I want the writer-model cost known and pinned.

## Business requirements

- BR-43.1 `.a`-`.z` keep their identity in by(, missing) panels, marker labels, tooltips and dropdown filters, both modes, before and after a move (G1).
- BR-43.2 Under `set dp comma`, ticks, tooltips, marker labels, KPI values and the CSV download use the comma decimal mark and the period thousands separator; dates are unchanged (G2).
- BR-43.3 `%tC` values convert with Stata's table; `Cofc`-measured instants round-trip (G2).
- BR-43.4 `graph set` fonts feed the three families, or the limit is documented with the probe's output (G2, D-43f).
- BR-43.5 `hover(x)`/`mlabel(count)` show the user's variable; `_dash_cell_cap` counts the planned embedding (G3).
- BR-43.6 Numeric carried columns reach Bokeh as arrays; the million-row line's build time falls (pinned relative, not absolute) (G4).
- BR-43.7 One writer per distinct (how, fmt, kind, storage, dp) per page; the help states the cost (G5).

## Technical requirements

- TR-43.1 (G4) `_carry_cols` per D-43g; docstring updated; `test_function_audit.py` entry unchanged.
- TR-43.2 (G1) `_dash_write_stata_data`: beside `cols[v]` build `ext = {i: code for i, x in enumerate(_column(v, missingval=None)) if x is None and <sfi says extended>}` -- read through `sfi.Missing` by `data.getAt` as `_dash_label_key` expects (`str(x)` of an extended missing is `".a"`); write `out["extendedMissing"] = {v: {str(i): code}}` when any. Loader: after the frame is built, for each key of `extendedMissing` add column `__dashm_<v>` (object dtype, `""` default). dash_parse.mata:2160's writer is unchanged (null) -- the code column is the renderer's.
- TR-43.3 (G1) `_dash_by_groups`: when `by_missing` and `__dashm_<v>` exists, the group key is `(value, code)`; the panel title for a missing value is the value label for jsonio key `_DASH_MISSING_LABEL_KEY + (ord(code) - ord('a') + 1)` if present, else `"." + code`, through `_dash_fmt_text`. `_apply_mlabel_opts`: a missing label value takes the code column's text. `_hover_tool`: for each hover variable with a code column, the tooltip field reads `@{v}{custom}` with the `CustomJSHover` writer receiving `special_vars`? No -- the writer's `code` reads `source.data["__dashm_" + name][index]` via its `args` (`src` and `name` added to `_dash_fmt_model_args`); `dash_fmt_text(value, fmt, storage, miss)` returns `miss` when non-empty. `_build_filter_widgets`: a dropdown over a variable with codes adds one option per distinct code, labelled by the same title rule, and the filter mask JS (`dash_filter_mask`) matches `__dashm_<v>` equality for those options (one `else if` in `_DASH_FILTER_MASK_JS`; this is the one JS edit of S43 and batch 14 -- no other batch-14 section edits `_FILTER_JS`/`_DASH_FILTER_MASK_JS`).
- TR-43.4 (G2 dp) dash.ado: `"dp":"`c(dp)'"` written into build_options beside `level`. `_dash_fmt`/`_dash_fmt_text` gain `dp="period"`; `_dash_fmt_parse`-level: in `_dash_fmt_number`, when `dp == "comma"` swap the roles of `.` and `,`. JS: `dash_fmt(value, fmt, storage, strip, dp)`, `dash_fmt_text(value, fmt, storage, dp, miss)`; `_dash_fmt_model_args` adds `dp`; `_DASH_FMT_MODEL_JS` passes it. Every caller passes `self.dp` (renderer attribute set in `render()` and in the served `make_document` from the spec). The CSV download writes the same marks (its writer calls `_dash_fmt_text`).
- TR-43.5 (G2 tC) module constant `_STATA_LEAP_SECONDS_TC_MS` (27 ints from the fixture, with a comment naming the fixture key `leap.table`), function `_dash_tc_from_tC(values)` (numpy, after `_dash_date_units` :535), called at :652 in place of the warning; copy list: constant after `"_DASH_BS_LG_FROM_PX"`'s group? No: after `_DASH_STALE_STATUS_HTML` per R2; function after `"_dash_reference_lines"`? R2 says functions after `_dash_reference_lines` (:47223): add `"_dash_tc_from_tC",` there. function_test_map.py entry.
- TR-43.6 (G2 fonts) per D-43f: dash.ado reads the measured home into `build_options["fontface"...]`; renderer `self.gt_fonts = dict(_DASH_GT_FONTS)` updated from the spec; `_dash_graph_text_runs`'s font resolution reads the dict passed down (today it returns the tag name as `font` and `_dash_graph_text_style` maps through `_DASH_GT_FONTS` -- change that lookup to `fig._dash_gt_fonts` stamped by `apply_to_figure`, as `_dash_size_ref_in` is).
- TR-43.7 (G3) `_carry_cols`: a colliding key is carried as `"__dashu_" + _k`; `GlyphMapper._user_field(name, data)` staticmethod; `_hover_tool` and `_apply_mlabel_opts` resolve through it; dash.ado's reserved-prefix message (:6555) lists `__dashu_*` and `__dashm_*`. `_dash_cell_cap`: the caller passes the planned count (the variables `_dash_plot` already assembles per graph for export: `_dash_export_vars` or its equivalent at :7300 region -- read the actual name before editing).
- TR-43.8 (G5) cache key `(how, fmt, kind, storage, dp)` shared by `_dash_fmt_tick_formatter` and the tooltip writer builder (`_dash_fmt_hover_formatter` or its name near :27960); `len(_DASH_FMT_JS)` written into the help's Performance paragraph as "about NN KB per distinct format".
- TR-43.9 Both renderers: `_dash_tc_from_tC` and the constant on the copy lists; `_user_field` is a class member; the loader and writers are shared module functions already copied (`_dash_load_columns`, `_dash_fmt*` are in the functions tuple -- confirm by grep and add any that is not after `"_dash_reference_lines",`). `_dash_write_stata_data` runs under Stata only. function_test_map.py: `_dash_tc_from_tC`, `GlyphMapper._user_field`. program_coverage_map.py: no new program unless dash.ado gains one for fonts (`_dash_graph_set_fonts` -> `test_wp31_truth.cscript:U43-04`).
- TR-43.10 Help (R3): dash.sthlp :2886-2892 (extended missing: now drawn), :1419-1423 (format paragraph: `set dp comma`), the `%tC` sentence (grep `leap`), :4066-4071 (fonts per D-43f), the Performance paragraph (writer cost), the reserved-prefix sentence (`__dashu_`, `__dashm_`). TWOWAY_COVERAGE_AUDIT.md:113 ("extended missing values collapse to `.`") gains `[WP-31 G1: corrected]`.


### Reference TR-43.A: the leap-second candidates the probe tests (IERS; `leap.table` keeps those where `Cofc()` steps)

30jun1972, 31dec1972, 31dec1973, 31dec1974, 31dec1975, 31dec1976, 31dec1977, 31dec1978, 31dec1979, 30jun1981, 30jun1982, 30jun1983, 30jun1985, 31dec1987, 31dec1989, 31dec1990, 30jun1992, 30jun1993, 30jun1994, 31dec1995, 30jun1997, 31dec1998, 31dec2005, 31dec2008, 30jun2012, 30jun2015, 31dec2016 (27). The do-file loops `foreach d in ...` computing `local t = tc(`d' 23:59:59.999) + 1` and `Cofc(`t') - `t'`; a step of 1000 ms from the previous candidate marks the instant. Python side:

```python
#: %tc instants (ms) after which Stata's %tC counts one more second
#: (test/fixtures/data_locale_truth.json leap.table, measured with Cofc(),
#: WP-31 G2).  27 entries; %tC = %tc + 1000 * (entries <= the instant).
_STATA_LEAP_SECONDS_TC_MS: tuple = (<27 ints from the fixture>)


def _dash_tc_from_tC(values):
    """%tc milliseconds of %tC values (cofC): subtract one second per
    leap second inserted at or before the instant.  NaN stays NaN."""
    v = np.asarray(values, dtype=float)
    table = np.asarray(_STATA_LEAP_SECONDS_TC_MS, dtype=float)
    # A %tC instant t_C lies after the k-th leap second when
    # t_C >= table[k] + 1000 * (k + 1); count those k.
    shifted = table + 1000.0 * np.arange(1, len(table) + 1)
    k = np.searchsorted(shifted, v, side="right")
    out = v - 1000.0 * k
    out[~np.isfinite(v)] = np.nan
    return out
```
`TestLeapSeconds::test_roundtrip` checks `_dash_tc_from_tC(C) == c` for the fixture's `(c, C)` pairs exactly (integers in float64).

### Reference TR-43.B: dp comma in the writers (TR-43.4)

Python, in `_dash_fmt_number(parsed, v, dp)` (re-read the function near :27700): after the digits are assembled with `.` and the thousands `,`, `if dp == "comma": text = text.replace(",", "\x00").replace(".", ",").replace("\x00", ".")`. JS twin, in `dash_fmt_number(parsed, v, dp)`: the same three replaces with `split`/`join`. The model code template `_DASH_FMT_MODEL_JS` passes `dp` from `args`; `_dash_fmt_model_args(fmt, kind, storage, dp)` adds `"dp": dp`. Fixture `dp.f` (`display %9.2f 3.14159` under comma) is the oracle: both writers must print it byte for byte.

### Reference TR-43.C: `_carry_cols` after S43 (TR-43.1 and TR-43.7)

```python
        for _k, _v in dict(getattr(source, "data", {}) or {}).items():
            _key = _k
            if _k in data:
                # A user variable named like a derived key (x, y, top, count,
                # density) is carried under a reserved alias (WP-31 G3).
                _key = "__dashu_" + _k
                if _key in data:
                    continue
            try:
                _col = np.asarray(_v)
                if _col.dtype.kind in "fiub":
                    _col = _col.astype(float)
                elif not np.issubdtype(_col.dtype, np.datetime64):
                    _col = np.asarray(_v, dtype=object)
                if selector is not None:
                    _col = _col[selector]
                if len(_col) != _n:
                    continue
                data[_key] = (_col if _col.dtype.kind in "fM" else _col.tolist())
            except (TypeError, ValueError, IndexError, KeyError):
                continue
        return data

    @staticmethod
    def _user_field(name, data):
        """The column a user variable *name* is carried under in *data*:
        its alias when a derived key shadows it (WP-31 G3)."""
        alias = "__dashu_" + str(name)
        return alias if alias in data else str(name)
```
`_hover_tool` builds each tooltip's field as `"@{%s}" % self._user_field(v, source.data)`; `_apply_mlabel_opts` reads `self._user_field(mlabel_var, source.data)`.

### Verbatim TR-43.D

- dash.ado build-options writer: the line `"dp":"`c(dp)'",` written beside `"level"` (grep `"level"` in `_dash_plot`'s JSON block); the reserved-prefix message at :6555 gains `, its user-variable aliases __dashu_* and its missing-code columns __dashm_*`.
- dash.sthlp :2888-2890 becomes: `{cmd:twoway} draws an extended missing value, {cmd:.a} to {cmd:.z}, as its value label or its name; so does {cmd:dash}: a {cmd:by(, missing)} panel is titled by it, a marker label and a tooltip show it, and a dropdown filter offers each code.`
- dash.sthlp format paragraph (:1419-1423) gains: `{cmd:set dp comma} is read: every number dash writes uses your decimal mark.`
- The `%tC` sentence becomes: `{cmd:%tC} values are converted with Stata's own leap-second table, so timestamps are exact.`
- Performance paragraph: `Each distinct display format on a page carries one formatter of about <NN> KB (ticks and tooltips of one format share it).`
- CHANGELOG Results lines: `- .a-.z drew as one missing value; they draw apart (WP-31, G1)`, `- numbers ignored set dp comma; they use it. %tC timestamps were up to 27 s off; they are exact (WP-31, G2)`; Requirements line: none.
- BUGS.md G3b open form: `- [ ] Title: The data file embeds numbers as JSON text (about 0.5 GB per million values)` / `File Names and Line Numbers: dash_render.py _dash_write_stata_data, dash_parse.mata _dash_json_number17` / `Description: GAPS3.md G3, re-verified at 6370ca4: ...` / `Suggested fix: a binary (base64 float64) column form read by both renderers and the served route` / `Resolution: Not fixed because WP-31 section 43 closed G3's shadowing and count parts only. Graded S3 (WP-31): a size cost, not a wrong picture.` G3c the same form for the strL per-observation loop.

## Boundaries

- No binary data file, no strL loop change (D-43d residuals); no change to `_dash_json_number17`.
- The `"(missing)"` dropdown option and multi-select are S49's; S43 adds code options only.
- `_FILTER_JS` body untouched except the one `_DASH_FILTER_MASK_JS` branch (TR-43.3); the KPI block, histogram/kdensity branches and the stale cue are not edited.
- No new dependency (M22); `_dash_tc_from_tC` is numpy.

## Stata truth

Script `scripts/extract_data_locale_truth.do` -> `test/fixtures/data_locale_truth.json`.

| Key | Probe | Recorded |
|---|---|---|
| `em.by_missing` | auto with `rep78` recoded: `.a` for 2 rows, `.b` for 3; `twoway scatter mpg weight, by(rep78, missing)`; SVG | rc; panel count; the missing panels' titles (text) |
| `em.by_missing_labelled` | same with `label define` `.a "Not asked"` on rep78's label | titles |
| `em.mlabel` | `scatter mpg weight, mlabel(rep78)` | the label text drawn for the `.a` rows |
| `dp.f`, `dp.fc`, `dp.g`, `dp.td` | `set dp comma`; `display %9.2f 3.14159`, `display %12.2fc 1234567.891`, `display %9.0g 0.5`, `display %td 20000` | printed text |
| `dp.axis` | `set dp comma; scatter mpg weight`; SVG tick labels | tick label texts |
| `leap.table` | for each of the 27 IERS dates d: `Cofc(tc(d 23:59:59.999) + 1) - (tc(d 23:59:59.999) + 1)` and the same at d-1 | the 27 `%tc` instants where the difference steps, in ms |
| `leap.roundtrip` | 20 random `%tC` values 1972-2026: `cofC()` | pairs |
| `fonts.home` | `graph set svg fontface Courier`; `graph set window fontface Courier`; capture `graph set`, `graph query`, `macro list`, `char list` to a log | the log text; whether a readable home exists and its access form |
| `fonts.svg` | `scatter ..., title("{stSans:a}")` after `graph set svg fontface Courier`; SVG | the title's `font-family` |
| `shadow.hover` | auto with `generate x = price`; `scatter mpg weight` (twoway has no hover; record only that twoway accepts the variable name) | rc |

Truth block `* ==== S43 G1 G2 G3 G4 G5: Extended missing values and locale ====`: U43-01 fixture stamped; U43-02 dash's by(, missing) panel count and titles equal `em.*` in both modes (python helper over the spec); U43-03 under `set dp comma` dash's tick labels and a tooltip's text equal `dp.*` (python helper runs `_dash_fmt` and the JS twin under node through `js_runner`); U43-04 fonts per D-43f (either the family contains Courier in both modes or the help quotes the probe); U43-05 `%tC` round trip: dash's conversion of `leap.roundtrip` values equals `cofC()`'s; U43-06 `hover(x)` with a user variable `x` shows the user's values in both modes; U43-07 `_dash_cell_cap`'s count on a frame with one computed-only graph equals the planned count (log text); U43-08 the data file holds `extendedMissing` for `rep78` and the served app lists `.a` in the dropdown.

## TDD test stubs

### `test/test_extended_missing.py` (new)

- Test: fixture stamped -- `TestTheFixture::test_meta` (guard).
- Test: the data writer emits `extendedMissing` for a frame with `.a`/`.b` (through `conftest.make_data_json` extended with codes) and the loader builds `__dashm_rep78` -- `TestTheDataPath::test_writer_emits_codes`, `::test_loader_builds_code_column` (red: KeyError).
- Test: by(rep78, missing) draws the fixture's panel count and titles, both modes; labelled code uses its label -- `TestByMissing::test_panels[mode]`, `::test_labelled[mode]` (red: one panel).
- Test: marker labels and tooltips show `.a` -- `TestLabelsAndTooltips::test_mlabel[mode]`, `::test_tooltip_js_twin` (node), `::test_served_tooltip` (red).
- Test: a dropdown over rep78 offers `.a` and `.b`; selecting `.a` keeps those rows (saved JS under node; served) -- `TestFilters::test_options[mode]`, `::test_move[mode]` (red).
- Test: after a move the code column follows the rows -- `TestAfterAMove::test_saved`, `::test_served` (red).

### `test/test_display_format_writer.py` (append)

- `TestDpComma::test_python_writer[case]` (fixture `dp.*`; red), `::test_js_twin[case]` (red), `::test_every_fmt_caller_passes_dp` (red), `::test_axis_ticks_both_modes[mode]` (red), `::test_dates_unchanged` (guard).
- `TestLeapSeconds::test_table_is_statas` (27 instants == fixture; red), `::test_roundtrip[case]` (red), `::test_no_warning` (red: warns), `::test_tooltip_is_statas[mode]` (red).
- `TestOneWriterPerQuadruple::test_no_duplicate_models[mode]` (red if tooltips and ticks of one format make two), `::test_help_states_the_size` (red).

### `test/test_graph_text.py` (append)

- `TestGraphSetFonts::test_face_reaches_the_families[mode]` or `::test_limit_is_documented` by D-43f (red).

### `test/test_carry_cols.py` (new)

- `TestArrays::test_numeric_stays_array`, `::test_int_becomes_float_array`, `::test_text_is_list`, `::test_dates_stay_arrays`, `::test_selector_applies` (red: lists); `::test_build_is_faster_than_lists` (relative: a 200,000-row carry under arrays is under half the list time; marked `slow`).
- `TestUserFieldShadowing::test_hover_x[mode]`, `::test_mlabel_count[mode]`, `::test_reserved_alias_prefix_refused_in_ado` (cscript U43-06 covers the ado half) (red).
- `TestCellCap::test_counts_planned_rows` (cscript U43-07; pytest half reads `_dash_cell_cap`'s message from a captured log fixture) (red).

### Flips

From `<scratch>/s43/43-flips.txt` (panel counts, `.a` as `.`, list comparisons, the `%tC` warning node, `dash_fmt` arity); reasons "twoway keeps .a-.z apart (G1)", "`set dp comma` is read (G2)", "%tC converts with Stata's table (G2)", "carried numeric columns are arrays (G4)".

### cscript: U43-01..U43-08. Parity (R8): `CORPUS` "by(rep78, missing) with .a .b", "hover(x) user variable x", "set dp comma ticks"; `MOVE_CORPUS` "dropdown to .a".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| Extended missing path | pytest test_extended_missing.py + U43-02/08 | data_locale_truth.json | yes |
| dp comma | pytest TestDpComma + U43-03 | same | yes |
| Leap seconds | pytest TestLeapSeconds + U43-05 | same | yes |
| Fonts | pytest TestGraphSetFonts + U43-04 | same | yes |
| Shadowing, cell cap | test_carry_cols.py + U43-06/07 | -- | yes |
| Arrays | test_carry_cols.py | -- | n/a |
| Writers per page | pytest TestOneWriterPerQuadruple | -- | yes |

AC-43.1..AC-43.7 one per BR; AC-43.8 five green commits, two residual entries open with Graded clauses.

## Tasks

**Commit boundary.** 43-01 tests (no commit); 43-02 commits G4 `Keep numeric carried columns as arrays (WP-31 G4)` then G1 `Carry extended missing values .a-.z through panels, labels, tooltips and filters (WP-31 G1)`; 43-03 commits G2 `Read set dp comma, convert %tC with Stata's leap seconds, read graph set fonts (WP-31 G2)`; 43-04 commits G3 `Carry user variables named like derived keys under a reserved alias and count the planned embedding (WP-31 G3)` then G5 `Share one format writer per distinct format per page and document its cost (WP-31 G5)`, then hands back. `$WT=<worktrees>/wp31-s43`.

<task type="auto" id="43-01">
  <name>Measure Stata's locale and missing rules, write failing tests</name>
  <files>scripts/extract_data_locale_truth.do, test/fixtures/data_locale_truth.json, test/test_extended_missing.py</files>
  <action><![CDATA[
    Check the worktree (wp31-s43, batch-14 base). Create the extractor from the table (head as scripts/extract_date_axes_truth.do; `leap.table` computed in Stata with `Cofc()`; logs captured with `log using` and read by the python block; `_meta` five keys); run through the slot; `git add -f` the fixture; record `len(_DASH_FMT_JS)` with `python3 -c "import dash_render as d;print(len(d._DASH_FMT_JS))"` into `<scratch>/s43/fmtjs_bytes.txt`. Create test/test_extended_missing.py and test/test_carry_cols.py with the stub classes; append the stub classes to test/test_display_format_writer.py and test/test_graph_text.py (at the end). Run the four files `-q -n0 -p no:cacheprovider -rf > <scratch>/s43/43-01.log`; write `<scratch>/43-01-failure.txt` grouped by row. Write U43-01..U43-08 in the S43 block; run (`WP31_ONLY=S43`); append FAIL lines. Simulated fix on a scratch copy for TR-43.1..TR-43.8: run test_by*.py, test_dates.py, test_display_format_writer.py, test_hover*.py, test_marker_label_parity.py, test_string_value_export.py, test_label_sinks.py -> `<scratch>/s43/43-flips.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/data_locale_truth.json'));print(sorted(d['_meta']), len(d['leap.table']), 'fonts.home' in d)"` prints the five keys, 27, True; `grep -c FAILED <scratch>/s43/43-01.log` is at least 25; `grep -c "U43-0[2-8] FAIL" <scratch>/s43/run_test_wp31_truth.log` is at least 6; `test -s <scratch>/43-01-failure.txt`.]]></verify>
  <done>Stata's by(, missing) titles, dp comma output, leap-second table, font storage and the probes' rc were recorded, and every regression test and truth case was shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="43-02">
  <name>Keep arrays, carry extended missing codes, commit G4 and G1</name>
  <files>dash_render.py, dash.ado, BUGS.md</files>
  <action><![CDATA[
    Apply TR-43.1; flip the list-comparison nodes; run test_carry_cols.py::TestArrays, the flipped files, test_saved_filter_layers.py, test_mode_parity.py -k hover; close BUGS.md G4, Tracked line, marker; commit `(WP-31 G4)`. Then apply TR-43.2 and TR-43.3 (the one `_DASH_FILTER_MASK_JS` branch; the dropdown code options; by() keys; mlabel; tooltip writer args), dash.ado's reserved-prefix message, dash.sthlp :2886-2892 and TWOWAY_COVERAGE_AUDIT.md:113; flip the panel-count and `.a`-as-`.` nodes; run test_extended_missing.py, the flipped files, test_label_sinks.py, test_csp.py, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_mode_parity.py -k missing, and U43-02/U43-08; close G1; commit `(WP-31 G1)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_carry_cols.py -k Arrays test/test_extended_missing.py test/test_csp.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U43-0[28] PASS" <scratch>/s43/run_test_wp31_truth.log` prints 2; `git log --format=%s -2 | grep -c "(WP-31 G[14])"` prints 2.]]></verify>
  <done>Numeric carried columns reach Bokeh as arrays and extended missing values keep their letter in panels, labels, tooltips and dropdown filters in both modes; the G4 and G1 commits landed.</done>
</task>

<task type="auto" id="43-03">
  <name>Read dp comma, leap seconds and graph set fonts, commit G2</name>
  <files>dash_render.py, dash.ado, test/test_display_format_writer.py</files>
  <action><![CDATA[
    Apply TR-43.4 (every `_dash_fmt`/`_dash_fmt_text` caller passes `dp`; the JS twin; model args), TR-43.5 (constant from `leap.table`; `_dash_tc_from_tC`; copy-list entries after `_DASH_STALE_STATUS_HTML` and `_dash_reference_lines`; function_test_map entries; delete the warning :654-660), TR-43.6 by `fonts.home` (D-43f; a new dash.ado program joins `_dash_require_mata`? no -- it is ado, so program_coverage_map.py only). Flip the `%tC` warning node and `dash_fmt` arity nodes. Update the help (:1419-1423, the `%tC` sentence, :4066-4071). Run test_display_format_writer.py, test_dates.py, test_graph_text.py::TestGraphSetFonts, test_label_sinks.py::TestJavaScript, test_statistical_helpers.py::TestTheServedAppCarriesEveryName, test_function_test_map.py, test_program_coverage_map.py, and U43-03/04/05. Close BUGS.md G2 (if fonts are documented-only, the Resolution says so with the probe's quoted output; no residual: M17), Tracked line, markers (Results line for `%tC`; Changed-behaviour none). Commit `(WP-31 G2)`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_writer.py test/test_dates.py test/test_graph_text.py -k "GraphSetFonts or Dp or Leap" test/test_function_test_map.py -q -p no:cacheprovider` ends 0 failed; `grep -c "U43-0[345] PASS" <scratch>/s43/run_test_wp31_truth.log` prints 3; `grep -c "leap-second-corrected millisecond count" dash_render.py` prints 0; `git log -1 --format=%s` ends `(WP-31 G2)`.]]></verify>
  <done>Every number writer honours set dp comma in Python and JavaScript, %tC converts with Stata's measured leap-second table without a warning, and graph set fonts are read or their limit documented; the G2 commit landed.</done>
</task>

<task type="auto" id="43-04">
  <name>Alias shadowed user variables, count planned rows, share writers, commit G3 and G5</name>
  <files>dash_render.py, dash.ado, BUGS.md</files>
  <action><![CDATA[
    Apply TR-43.7 (`_user_field`; `_hover_tool`, `_apply_mlabel_opts`; `_dash_cell_cap`'s planned count from the variables `_dash_plot` assembles -- read dash.ado:7300-7460 to find the export variable list's local name before editing); dash.sthlp's reserved-prefix sentence; run test_carry_cols.py::TestUserFieldShadowing, ::TestCellCap, test_hover*.py, test_marker_label*.py, test_cell_cap*.cscript through the driver if one exists (else U43-07), U43-06; open the two residual entries G3b/G3c in BUGS.md (BRIEF's open form, `Graded S3 (WP-31): <why>`), close G3's entry, rewrite `G3 Tracked` as "Partly closed in WP-31 (section 43, commit <sha>): shadowing and the planned count; open: binary data file, strL loop (BUGS.md "<G3b title>", "<G3c title>")", marker; commit `(WP-31 G3)`. Then apply TR-43.8 (key shape, shared cache, help Performance paragraph with `<scratch>/s43/fmtjs_bytes.txt`'s number in KB); run test_display_format_writer.py::TestOneWriterPerQuadruple, test_help_conformance.py, test_mode_parity.py -k format; close G5 (Resolution names D-43e), Tracked, marker; commit `(WP-31 G5)`. Run the four new/extended test files whole and the S43 block once more; write `<scratch>/s43/handback.txt` (five shas; D-43d and D-43e for ratification; D-43f's branch with the probe text).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_extended_missing.py test/test_carry_cols.py test/test_display_format_writer.py test/test_help_conformance.py test/test_tracking_documents.py -q -p no:cacheprovider` ends 0 failed; `grep -c FAIL <scratch>/s43/run_test_wp31_truth.log` prints 0; `git log --format=%s <base>..HEAD | grep -c "(WP-31 G"` prints 5; `grep -c '^- \*\*G3 Tracked:\*\* Partly closed' GAPS3.md` prints 1; `test -s <scratch>/s43/handback.txt`.]]></verify>
  <done>User variables named like derived keys reach hover() and mlabel() through a reserved alias, the cell cap counts the planned embedding, one writer model exists per distinct format per page with its cost documented, and S43's five commits were verified green with two residual entries open.</done>
</task>

## Section completion criteria

- `.a`-`.z` drawn apart at every sink in both modes and after moves; `set dp comma` honoured by every writer; `%tC` exact; fonts read or documented; shadowed names aliased; planned count; arrays; one writer per quadruple with the cost documented.
- Five green commits; BUGS.md G1, G2, G4, G5 closed, G3 closed with G3b/G3c open (Graded); Tracked lines; markers; fixture stamped and named.

## Notes

- **Renderer order:** the loader runs before any mapper in both modes; the served `make_document` reads the same data file (base64), so `extendedMissing` must be read in `_dash_load_columns`, not in `DashRenderer.render`.
- **R12:** S43 is batch 14's only `_DASH_FILTER_MASK_JS` editor (one `else if`); `_build_filter_widgets` edit is the dropdown options list only -- also batch 14's only editor (S41/S42 do not touch it).
- **Copy lists (R2):** `_STATA_LEAP_SECONDS_TC_MS` after `_DASH_STALE_STATUS_HTML`'s group; `_dash_tc_from_tC` after `"_dash_reference_lines",`; everything else is already copied or a class member.
- **R6:** `version 19` in any new dash.ado program; the seven key lists unchanged (`dp` is a build option).
- **R10:** test_unsupported_report_is_true.py untouched.
- **For S49 (batch 16):** dropdown code options are `(label, "__dashm_<v>=a")` values; the `"(missing)"` toggle must treat `.` and the codes as one group only when the user asks.
- **For S48 (data table):** show `__dashm_<v>`'s code in place of `.` for the variable's column.
- **python_exec hazard** as S40.
- **Decisions for ratification:** D-43d (G3 partly closed; two residuals), D-43e (G5 closed by one-per-quadruple plus documented cost), D-43f's branch if fonts are documented-only.
