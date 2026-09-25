# Section 04: Display-format writer core

> Part of: WP-28 · Gaps: E1, E3, G6 (foundation) · Risk: red · Batch: 2 · Depends on: 03 · Blocks: 11, 12 


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **2** · Depends on **03** · Blocks **11, 12** · Risk **red** · Commits: one commit (S04); no gap entry (E1/E3/G6 close in S11/S12)

- D10: task 04-04's verify arithmetic is wrong (feasibility.md critical 4: 14977.0, not 15341.0) — re-derive and show the derivation.
- D10: add a unit test for `dash_html_escape` and its Python twin; add a width-1 format stub; the JS twin tests use `run_js` from `test/js_runner.py`, not a fifth private node runner.
- D7: split 04-01, 04-03, 04-05, 04-07 as feasibility.md proposes.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) are applied to this file in the fixer pass; until then this block governs.

## Overview

dash promises that a number or a date on the page reads as Stata shows it. Today it has
no writer for Stata's display formats: `_parse_stata_numeric_fmt` (dash_render.py:839)
reads only `%w.d[f|e][c]`, so Stata's *default* `%9.0g` and every `%g`, `%gc`, European
comma and `%t` picture fall through to Python's `format()`, to `f"{v:g}"`, to
`str(value)` or to one fixed date picture per kind. GAPS2 measured the symptoms:
`fmt(%10.0g)` of 6165.2567 shows `6e+03` in both modes and after every move; `%9,2f`,
`%21x` and `%16H` show the raw value; `%td` of 15000 shows `15000.0`; a %td dropdown lists
`2001-12-31 00:00:00`; a %tm axis reads `Jan 2000` where twoway shows `2000m1`; a float
0.1 shows as `0.10000000149011612`; and `_dash_format_kpi_value(1234567.5, "%9.0g")` gives
`1.23457e+06` where Stata's rule gives `1234568`.

This section builds the one thing the three gaps share and nothing they do not: a Stata
display-format writer in Python with a byte-identical JavaScript twin, a Stata-measured
fixture of `display` outputs that pins both, the export of each variable's storage type,
the loaders carrying every writable format (and the served app the full format map), the
refusal of the formats the page cannot write (`%x`, `%H`, `%L`) with r(198) at `dash kpi
fmt()` time and a one-line fallback for a variable's own such format, and the test-map
entries. It changes **no page text** except what the widened loaders reach on their own,
which is named in §Evidence and flipped here. The fourteen number-to-text sites are
sections 11 (cards) and 12 (widgets, tooltips, axes, marker labels, CSV).

Why one section: DISCOVERY Q6 fixes one formatter module for every site; the `%w.0g` rule
is documented only by examples (PRD §10 risk 1), so the fixture and the writer must land
together, before any site consumes them, or every consumer would pin a guessed rule.

**Test order (CLAUDE.md rule 7): task 04-01 writes every failing test for this section**,
runs them against the unmodified tree and records the failure; 04-02 records Stata's
truth; 04-03 through 04-08 turn the tests green; 04-09 documents.

## Risk: [red] — the `%w.0g` rule is derived from examples, and two writers in two languages must agree byte for byte on about a thousand measured strings

**Why.** No stdlib function in Python or JavaScript reproduces Stata's width-driven `%w.dg`
(RESEARCH §1; report W §4); `String(x)` and `str(x)` disagree between 1e-6 and 1e-4 and
between 1e16 and 1e21 and on exponent padding (W §2), so neither twin may fall back to its
language's own number-to-text. A wrong rule here ships silently into every card, label
and tooltip.

**Risk factors.** (1) The derived `%w.0g` rule may be wrong on values nobody looked at.
(2) A `%t` picture has 40-odd codes and Stata's own maximum-width padding. (3) The served
app copies functions by source, so a helper missed from the copy lists is a `NameError`
at draw time. (4) The loaders now carry `%g`; any consumer that reads `numeric_formats`
today and cannot write `%g` would print worse text than before.

**Mitigation.** (1) `test/fixtures/format_truth.json` holds every `display` string Stata
printed, exactly, padding included, and the Python and node twins are compared to it row
for row in one test each; the plan states the hypothesis and the fixture decides. (2) The
picture codes are one ordered table in both twins, pinned by custom pictures in the
fixture. (3) `TestTheServedAppCarriesEveryName` and
`TestTheServedAppDefinesEveryNameItReads` fail the build on a missed name; the tasks name
the copy lists. (4) The two consumers that would mis-write `%g` are routed through the new
writer in the same commit (`_format_stata_numeric`) or guarded until section 11 removes
the guard (`_dash_effective_kpi_fmt`).

## Dependencies

- Depends on: none (batch 1; disjoint from every other batch-1 section: it edits the
  format helpers at 236-360 and 839-938, the writer 1214-1376, `_dash_load_columns`
  635-697, the copy lists, `_dash_validate_value`'s format kind in dash.ado, and adds
  new module-level functions).
- Blocks: section 11 (KPI cards), section 12 (widgets, tooltips, axes, labels, CSV).
- Parallel batch: 1. Can run with S01, S02, S03, S05, S06, S07, S08, S09, S10. S05
  edits `_FILTER_JS` at 14768-14834 (histogram recount); this section prepends a constant
  to `_DASH_FILTER_MASK_JS` (14110) and touches no line of `_FILTER_JS`'s body, so
  `patch -p1` merges cleanly.

## Evidence

### The helpers that exist, and what each cannot do

`_parse_stata_numeric_fmt`, dash_render.py:839-867 (report B §1.1):

```python
 853    m = re.fullmatch(r"%(-)?(\d+)\.(\d+)(f|e)(c)?", fmt.strip())
 ...
 862    if len(m.group(2)) > 4 or len(m.group(3)) > 4:
 863        return None
 864    width, dec = int(m.group(2)), int(m.group(3))
 865    if not 1 <= width <= 2045 or dec >= width:
 866        return None
```

The docstring says why: "`%g` is Stata's DEFAULT numeric format and expresses no user
intent, so it is deliberately not reproduced". The bounds (four-digit width and decimals,
width ≤ 2045, decimals < width) are WP-20's security fix against a billion-zero pattern
and **must be kept** in the new parser (`test_adversarial_matrix.py::TestNumericFormatBounds`).

`_format_stata_numeric`, :892-938: the `e` branch is `f"{val:.{dec}e}"`, which ignores the
width; `date_truth.json` records `%9.3e` of 1234.5678 as ` 1.23e+03`. Its `f` branch
passes all 56 measured `f`/`fc` cases with the rule "commas dropped when they overflow,
then two-decimal exponent" — but tests `len(plain) <= width`, while every measured
positive value fits in `width - 1` columns (the sign column), so a value of exactly `w`
digits is untested.

`_format_date_value_standalone`, :289-332, one fixed picture per kind:

```python
 323        if kind == "ty":
 324            return year
 325        if kind in ("tc", "tC"):
 326            return f"{ts.strftime('%d %b')} {year} {ts.strftime('%H:%M:%S')}"
 327        if kind in ("tm", "tq", "th"):
 328            return f"{ts.strftime('%b')} {year}"
 329        return f"{ts.strftime('%d %b')} {year}"
```

Stata writes `09jan2002`, `2000m10`, `2000q3`, `2000h2`, `1960w1` (report D §8b). This
function stays in this section (section 12 retires it) but nothing new calls it.

`_dash_unix_ms_to_unit`, :16214-16258: epoch milliseconds to Stata units `d w m q h y`
**with the fraction of the period elapsed**. It is the inverse the writer needs: a date
column is held as datetime64[ms] (`_dash_load_columns`, :635), so a formatter must first
recover the Stata value. `_STATA_EPOCH_UNIX_MS = -315_619_200_000` (:260) and
`_STATA_MS_MIN`/`_STATA_MS_MAX` (:258-259) bound Stata's range, 01jan0100 to 31dec9999.

### The loaders drop every format but `%f`

`_dash_load_columns`, :635-697:

```python
 672            if _stata_numeric_pattern(fmt) is not None:
 673                numeric_formats[col] = fmt
```

and the served twin `_NUM_FORMATS`, :24930-24934, with the same predicate:

```python
24930            "_NUM_FORMATS = %r" % ({
24931                str(_k): str(_v)
24932                for _k, _v in (self.spec.get("build_options", {})
24933                               .get("formats", {}) or {}).items()
24934                if _stata_numeric_pattern(str(_v))},),
```

So auto's `price` (`%8.0gc`) arrives with no format and a card on it falls back to `%9.0g`
(`_dash_effective_kpi_fmt`, :19591-19606). The saved renderer keeps the full map as
`self.formats` (:21170-21175); the served app keeps only `_NUM_FORMATS` and
`meta['date_vars']` (kind only, :25749-25756), so a custom picture such as
`%tdCCYY-NN-DD` never reaches a served page (report B §1.4).

### The export sends no storage type

`_dash_write_stata_data`, :1214-1376, writes `variableIsString` and `float(x)` per cell:

```python
1280    for v in names:
1281        is_str[v] = bool(data.isVarTypeString(v))
1282        if not is_str[v]:
1283            # Every missing value, . and .a to .z, as None: jsonio's "null".
1284            cols[v] = ["null" if x is None else float(x)
1285                       for x in _column(v, missingval=None)]
```

The document's keys are asserted as an exact set in
`test/test_string_value_export.py:284-287`; the stand-in `FakeSfi` (:78-130) carries a
`types` map and `isVarTypeString`/`isVarTypeStrL` but no `getVarType`. dash.ado sends the
display formats through `_dash_formats_json` (dash.ado:4075-4121, `st_varformat` read in
Mata, JSON-escaped) into `build_options.formats`.

### `dash kpi fmt()` accepts what the page cannot write

dash.ado:2294-2313, kind `format` of `_dash_validate_value` (:1948), whose only `format`
caller is `dash kpi` (:6238):

```stata
2306        if regexm(scalar(`V'), "^%[A-Za-z0-9_.,:!/+-]+$") & strlen(scalar(`V')) <= 60 {
2307            capture confirm numeric format `macval(value)'
2308            if !_rc local ok = 1
2309        }
2310        if !`ok' {
2311            mata: _dash_say("err", "`prefix': `opt'() must be a numeric display format such as %9.2f or %12.0fc (got: ", st_local("value"), ")")
2312            exit 198
2313        }
```

`confirm numeric format` is rc 0 for `%21x` and `%16H` (`test/fixtures/value_truth.json`
F9, F10) and the comment at :2299-2300 says so. Stata's own card text is
`kpi_display` (:6331-6335, `: display `fmt' `kpi_value'` then `strtrim`), and it travels
as `"display"` in `kpis_json` (:6974) — the truth value section 11's tests read.

### The served app is assembled by copying

Constants are copied by name at :24326-24428 (`_DASH_CSV_SERVED_JS` at :24408 is the
pattern for a JavaScript string constant), functions at :24466-24687, the three classes at
:24698-24700. A new module-level function that any copied function or `GlyphMapper` calls
must be in the function list, and every table it reads in the constant list
(`_dash_kpi_pctile`'s docstring, :19556, explains why a regex is inlined instead).

### The JavaScript strings the twin must reach

`_DASH_FILTER_MASK_JS` (:14110) heads both `_FILTER_JS` (:14177) and `_DASH_CSV_SAVED_JS`
(:14168); `_DASH_CSV_SERVED_JS` (:14081) is `_DASH_CSV_JS` (:14012) plus its own tail; the
brush code is assembled at :23478-23496 from slices of `_FILTER_JS` plus `_BRUSH_JS`
(:14935). The legacy number writers `dash_tie_even` … `dash_numfmt` (:14378-14482) have
exactly one caller, `dash_apply_kpis` at :14612; section 11 retires them.

### Stata's rules (report D §8; citations to `$BASE` = `/Applications/StataNow/ado/base/`)

- Grammar ([U] 12.5.1, `u.txt:4729-4805`): `%` `[-]` `[0]` `w` `.` `d` `{e|f|g}` `[c]`;
  d < w; the `0` flag is honoured only with `f`; comma may replace the point in any of them
  (`format.sthlp:84-88`: `%9,2fc` shows 1000.03 as `1.000,03`). Defaults by type: byte/int
  `%8.0g`, long `%12.0g`, float `%9.0g`, double `%10.0g` (`format.sthlp:159-166`).
- `%g` (`format.sthlp:292-325`): d=0 lets Stata choose the decimals; "it will switch to a
  %e format if the number is too large or too small". Documented examples: `%12.0g` 5.139
  → `5.139`, 5231371222.139 → `5231371222`, 52313712223.139 → `5.23137e+10`, 0.0000029394
  → `2.93940e-06`; `%9.0g` 10,000,000 → `1.00e+07`; `%9.4g` 31415.9265 → `31416`.
- Measured today (report W §4, StataMP batch): `%9.0g` 3.14159265 → `3.141593`, 123456789
  → `1.23e+08`, 12345678 → `1.23e+07`, 1234567.891 → `1234568`, -123456.789 → `-123456.8`,
  0.0001 → `.0001`, 0.000012345 → `.0000123`, 1e-7 → `1.00e-07`, 1e16 → `1.00e+16`;
  `%10.0gc` 12345678 → `12345678` (commas dropped), 1000.03 → `1,000.03`; `%9,0g`
  3.14159265 → `3,141593`; `%12,2gc` 1234567.891 → `1.234.568`.
- **Derived rule (the plan's hypothesis; the fixture decides).** A positive value is laid
  out in `w-1` columns (one column is reserved for a sign), a negative in `w`. `%w.0g`
  shows at most `w-2` significant digits in fixed form, drops trailing zeros and the `0`
  before the point; it switches to exponent form — a `w-6`-digit mantissa, `e±XX` — when
  the integer part needs more than `w-2` digits **or** the fixed form would keep fewer
  significant digits than the exponent form's `w-6` (`.0000123` keeps three and stays
  fixed; `.0000001` keeps one and becomes `1.00e-07`). `%w.dg` with d>0 shows
  `max(d, integer digits)` significant digits, capped at `w-2`. `%w.dgc` groups the
  integer part and drops the commas when the grouped form does not fit. `%w.df` shows
  d decimals, drops the commas of `fc` when they do not fit, and falls back to a
  two-decimal exponent when the plain form does not fit. `%w.de` shows d mantissa
  decimals and shrinks them to fit the width (`%9.3e` → `1.23e+03`). Exponents are two
  digits, three when needed, then one mantissa decimal fewer. `%0w.df` pads with zeros to
  the width; `%-w` left-aligns; the European comma swaps `.` and `,` after grouping.
- `%21x`, `%16H`/`%16L`/`%8H`/`%8L` are hexadecimal and IEEE byte dumps
  (`format.sthlp:364-429`): refused (DISCOVERY Q6). Invalid formats are r(120) "invalid
  %format" in Stata (`p.txt:9603`); dash's refusal code is r(198) (BRIEF, PRD §3).
- Dates (`$BASE/d/datetime_display_formats.sthlp:27-127`): heads `%tc %tC %td %tw %tm %tq
  %th %ty` plus optional details; codes `CC cc YY yy JJJ jjj Month Mon month mon NN nn DD dd
  DAYNAME Dayname Day Da day da h q WW ww HH Hh hH hh MM mm SS ss .s .ss .sss am a.m. AM
  A.M.`, literals `. , : - / \`, `_` a space, `+` nothing, `!c` any character. Default
  pictures: `%td` → `DDmonCCYY` (20jan2010), `%tc`/`%tC` → `DDmonCCYY_HH:MM:SS`, `%tw` →
  `CCYY!www` (1960w1), `%tm` → `CCYY!mnn` (2000m10), `%tq` → `CCYY!qq`, `%th` → `CCYY!hh`,
  `%ty` → `CCYY` (the year itself, `date_truth.json` `ty_is_the_year_itself`). Fractional
  seconds are omitted unless asked; times truncate, never round (`:272-287`). The period
  kinds are calendar periods (`date_truth.json` `%tm.note`), converted through
  `dofw/dofm/dofq/dofh`.
- Padding: `date_truth.json` records `%tm -120` as ` 1950m1` and `%9.0g 0` as
  `        0`: Stata right-aligns numbers to `w` and dates to the picture's maximum width.

### Fixtures on disk

- `test/fixtures/date_truth.json` (written by `scripts/extract_date_truth.do`): key
  `numeric_formats` → `{fmt: {values: [{value, display, display_cmd, display_width, rc,
  source}], comma_separated, constant_width, left_aligned, observed_widths, value_count}}`
  for 15 formats × 10 values (0, -1, ±1234.5678, ±1234567.891, 0.000123456, 1e12, `.`,
  `.a`); key `date_formats` → per kind `{values: [{value, display, display_cmd, display_rc,
  iso, iso_cmd, period_start_iso, period_end_iso, …}], epoch, …}` for all 8 kinds. No
  European comma, no `%x`/`%H`, no custom picture beyond the ISO ones. **Extended, not
  replaced**: this section adds `format_truth.json` beside it and leaves it untouched.
- `test/fixtures/value_truth.json` `formats`: 28 `confirm numeric format` return codes
  (`%21x` 0, `%16H` 0, `%9,2fc` 0, `%12s` 7). No display text.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_dates.py::TestNumericDisplayFormats::test_every_measured_f_and_fc_value_is_reproduced`
  (:446; exactly 56 cases from `date_truth.json`, stripped compare) — **stays green**:
  `_format_stata_numeric` delegates to the new writer and must still pass all 56.
- `test/test_dates.py::TestNumericDisplayFormats::test_an_unformattable_value_degrades`
  (:484; `""` for NaN) — stays: the wrapper keeps its `""` contract.
- `test/test_dates.py::TestNumericDisplayFormats::test_a_format_dash_does_not_reproduce_returns_none`
  (:488) and `::test_a_bokeh_tick_pattern_is_produced` (:480) pin `_stata_numeric_pattern`
  — **untouched here**; section 12 retires that function and flips them.
- `test/test_adversarial_matrix.py::TestNumericFormatBounds` (:1650-1695) — stays green;
  this section adds the same bounds for `_dash_fmt_parse` in Python and node.
- `test/test_string_value_export.py::TestTheWriter` key-set assertion (:284-287) —
  **flips**: the document gains `storageTypes`.
- `test/test_served_dates.py::TestOneColumnReader::test_the_reader_converts_dates_and_numbers`
  (:428-437) asserts `nfmts == {"n": "%9.2fc"}` — stays (an `f` format), and gains a `%g`
  case here.
- `test/test_option_validation.py::…::test_the_format_probes_agree_with_the_gate`
  (:1349-1364) reads `confirm`'s verdicts from `value_truth.json` — stays; the cscript gains
  the dash-side refusal cases.
- Page text reached by the widened loaders: marker labels of a variable whose display
  format is `%g`/`%e` (`_apply_mlabel_opts` `_numfmt` branch, :6759-6761) go from the raw
  number to Stata's text; `mlabformat(%w.de)` labels gain Stata's width rule. No committed
  test is known to pin either (the `_by`/`_dated` helpers pass only `%td` formats); task
  04-07 runs the full suite and flips any that does, naming each in the commit message.

## User stories

- **US-04.1** As a Stata user pasting twoway syntax, I want `dash kpi …, fmt(%21x)` (or
  `%16H`) refused with r(198) naming the format, so that a card never shows a raw number
  where I asked for a format the page cannot write.
- **US-04.2** As a dashboard viewer, I want a variable whose own display format is `%21x`
  drawn in `%9.0g` with one note at build time, so that the dashboard still renders and the
  author learns why the text differs.
- **US-04.3** As the maintainer, I want one Stata-measured fixture of `display` outputs and
  one test per twin against it, so that a wrong `%w.0g` rule fails loudly instead of
  shipping.
- **US-04.4** As the maintainer, I want the export to carry each variable's storage type and
  both loaders to carry every writable format and custom picture, so that sections 11 and
  12 can write `%8.0gc`, `%tdCCYY-NN-DD` and a float's digits in both modes.

## Business requirements

- **BR-04.1** For every numeric format Stata accepts other than `%x`/`%H`/`%L`
  (`%w.df`, `%w.dg`, `%w.de`, each with `c`, the `0` and `-` flags and the comma decimal)
  and every `%t` format with any picture, the writer's text equals Stata's `display` text
  for that value, character for character, padding included.
- **BR-04.2** The JavaScript writer's text equals the Python writer's text for the same
  inputs, on every fixture row and on the twin-disagreement ranges (1e-6…1e-4,
  1e16…1e21, exponent padding).
- **BR-04.3** A missing value is written as Stata writes it: `.`, padded to the width.
- **BR-04.4** `dash kpi …, fmt()` refuses `%x`, `%H` and `%L` formats with r(198) and a
  message naming the format; every other format `confirm numeric format` accepts is
  still accepted.
- **BR-04.5** A variable whose display format is `%x`/`%H`/`%L` is shown in `%9.0g` with
  exactly one note per variable per build, in both modes.
- **BR-04.6** A format Stata would refuse (width over 2045, decimals not below width,
  digit strings over four characters) is never written and never costs more than a
  second or 64 characters of output, in either twin.
- **BR-04.7** Nothing a user sees changes in this section except: marker labels of a
  variable whose own format is `%g` or `%e` now read as Stata writes them, and
  `mlabformat(%w.de)` follows Stata's width. Both are listed in CHANGELOG "Results that
  change".

## Technical requirements

- **TR-04.1 Module functions** (dash_render.py, module level, in the "One implementation,
  two callers" region so the copy list reaches them; every one added to the function copy
  list at 24466-24687 and to `test/function_test_map.py`):
  - `_dash_fmt_parse(fmt) -> dict | None`: `{"kind": "f"|"g"|"e"|"t"|"x"|"H", "width",
    "dec", "left", "zero", "group", "comma_dec", "tkind", "picture"}` or None. Numeric
    grammar `^%(-)?(0)?(\d{1,4})([.,])(\d{1,4})(f|g|e)(c)?$` with `1 <= width <= 2045`
    and `dec < width` (WP-20 bounds kept); `^%(-)?t([cCdhmqwy])(.*)$` gives kind `"t"`
    with `tkind` and `picture` (empty = default); `^%-?\d*x$` gives `"x"`; `^%-?\d*[HL]$`
    gives `"H"`. ASCII only (`fmt.isascii()`), at most 60 characters, no nested functions.
  - `_dash_fmt_kind(fmt) -> "f"|"g"|"e"|"t"|"x"|"H"|None`.
  - `_dash_fmt_refusal(fmt) -> str | None`: `"%21x is a hexadecimal display format the
    dashboard cannot write"` for `x`, the IEEE wording for `H`, `"%9.2 is not a display
    format dash writes"` for None; None for f/g/e/t.
  - `_dash_fmt_number(parsed, value) -> str` and `_dash_fmt_date(parsed, value) -> str`
    (private writers), `_dash_fmt_calendar(value, tkind) -> tuple` (Stata value → year,
    month, day, hour, minute, second, millisecond, day-of-year, week, weekday, half,
    quarter), `_dash_float32_text(value) -> str` (the shortest decimal that reads back as
    the same float32; JS-style exponent `1e-7`).
  - `_dash_fmt(value, fmt, storage=None, strip=False) -> str`: Stata's `display` text,
    right-aligned to the width (a date to the picture's maximum width; `%-` left-aligns).
    `value` is the Stata value (a number; for `%t` the Stata date number, never epoch
    milliseconds). None/NaN → `.` padded. `storage="float"` widens the value to the
    double Stata holds a float as (`float(np.float32(value))`) before writing; **task
    04-03 reads the fixture's float rows for `%12.0g` and `%20.0g` of 0.1 before choosing
    between "widen and write the double" and "write the shortest float32 digits" — both
    are one line, and the fixture, not this plan, picks.** A format `_dash_fmt_kind`
    returns None/x/H for is written in `%9.0g` (never raises; naming it is the caller's
    job through `_dash_fmt_refusal`). `strip=True` strips the padding.
  - `_dash_fmt_text(value, fmt, storage=None) -> str`: `_dash_fmt(..., strip=True)`; `.`
    for missing. The page-facing form.
  - `_dash_stata_value_of(column_value, date_kind) -> float | None`: epoch milliseconds
    (or a Timestamp/datetime64) back to the Stata value: `td` → days
    (`(ms - _STATA_EPOCH_UNIX_MS) / 86_400_000`), `tc`/`tC` → `ms - _STATA_EPOCH_UNIX_MS`
    (G7's leap seconds are out of scope: `tC` is written on `tc`'s epoch, as the loader
    converts it), `tw/tm/tq/th/ty` → `math.floor(_dash_unix_ms_to_unit(ms, unit))`;
    None for None/NaN/NaT or outside Stata's range.
- **TR-04.2 The numeric writer** implements the derived rule in §Evidence, hand-coded:
  no `format(x, "g")`, no `str(x)`, no `String(x)`, no `Intl`, no locale. Rounding is
  Stata's (round half away from zero on the decimal digits as `display` shows it; the
  fixture's ties — 1234567.5 under `%9.0g`, 20.5 under `%9.0f` — decide, and the current
  `dash_tie_even` comment at 14388 records that Python rounds a tie to even where Stata
  rounded up: the new Python writer rounds as Stata does, not as `round()` does).
  Grouping and the European comma: group with `,` then swap `.`↔`,` in one pass
  (`str.translate` / a single regex), never two `replace` calls (W §4).
- **TR-04.3 The date writer**: one ordered code table shared by both twins, longest match
  first: `DAYNAME Dayname Month month a.m. A.M. .sss JJJ jjj Mon mon Day day .ss` then
  `CC cc YY yy NN nn DD dd Da da WW ww HH Hh hH hh MM mm SS ss am AM .s` then `h q . , :
  - _ / \ +` and `!` + one character; any other character is a literal. The calendar of a
  period value is its first day (`dofw`, `dofm`, `dofq`, `dofh`, `dofy`); a `%td` value is
  floored; a `%tc` time is truncated to the code's precision. Python uses
  `datetime.date.fromordinal` arithmetic from 01jan1960 (year 100 is inside `date`'s
  range); JavaScript uses UTC `Date` arithmetic and **must set the year through
  `setUTCFullYear`, never `new Date(y, …)`, so years 100-999 are not remapped**. The
  maximum-width table for right-alignment (`nn` 2, `Month` 9, `Dayname` 9, `JJJ` 3, …)
  is pinned by the fixture's padded strings.
- **TR-04.4 The JavaScript twin** is one module-level string constant `_DASH_FMT_JS`
  defining `dash_fmt_parse`, `dash_fmt_kind`, `dash_fmt(value, fmt, storage)`,
  `dash_fmt_text(value, fmt, storage)`, `dash_stata_value_of(ms, kind)`,
  `dash_float32_text(v)` and `dash_html_escape(s)` (five characters, for section 11's card
  rebuild). It is prepended **once** to `_DASH_FILTER_MASK_JS` (so `_FILTER_JS` and
  `_DASH_CSV_SAVED_JS` carry it), once to `_DASH_CSV_SERVED_JS`, and at the brush wiring
  (`_DASH_FMT_JS + _pctl + _helpers + _BRUSH_JS`, :23483-23496); it is added to the
  constant copy list beside `_DASH_CSV_SERVED_JS` (:24408). A test asserts each shipped
  code string holds exactly one `function dash_fmt(`. `toFixed`/`toPrecision` arguments
  are clamped to 0..100 and widths to 2045 before use (rule 1). No `eval`, no `Function`,
  no template interpolation of the format into code: the format is always an argument.
- **TR-04.5 Export and loaders.** `_dash_write_stata_data` writes `"storageTypes":
  {var: data.getVarType(var)}` (`byte int long float double str# strL`) beside
  `variableIsString`; `FakeSfi.Data.getVarType` returns `fake.types[v]`. Saved
  `_load_data` (:21160-21187) sets `self.storage_types` (and pops qualifier columns as it
  pops formats); the served loader (:25734-25756) puts `storage_types` in `meta`, and the
  builder emits `_FORMATS = %r` (the **full** `bo['formats']` map, custom pictures
  included) beside `_NUM_FORMATS`. `_dash_attach_labels(..., storage_types=None)` sets
  `mapper.storage_types`; both callers pass it. `_dash_load_columns` keeps a numeric format
  when `_dash_fmt_kind(fmt) in ("f", "g", "e")`, and for a format whose
  `_dash_fmt_refusal` is not None warns once (`_dash_warn_once(("format", col), …)`, the
  BR-04.5 wording) and stores `%9.0g`; `_NUM_FORMATS` uses the same predicate.
- **TR-04.6 Consumers made safe in the same commit.** `_format_stata_numeric(value, fmt)`
  becomes a thin wrapper: `""` for a non-finite value, else `_dash_fmt_text(value, fmt)`
  (its 56 pinned cases stay green; its `%e` output gains the width rule).
  `_dash_effective_kpi_fmt` gains a **temporary guard** — the variable's own format is used
  only when `_dash_fmt_kind(own) == "f"` — with the comment "section 11 removes this
  guard", so a card on a `%g` variable is unchanged until the KPI writers move to
  `_dash_fmt` (report B §1.5 keeps `test_help_claims_4.py::TestACardKeepsItsFormatWhenAFilterMoves`).
- **TR-04.7 dash.ado.** In `_dash_validate_value` kind `format`, after `confirm numeric
  format` passes, refuse `regexm(scalar(`V'), "^%-?[0-9]*[xHL]$")` with
  `_dash_say("err", "`prefix': `opt'() cannot be written by the dashboard: ", <value>,
  " (hexadecimal %x and IEEE %H/%L formats are refused)")` and `exit 198`. The value is
  echoed by `_dash_say`, never expanded into the line (as :2311 does).
- **TR-04.8 Fixture.** `scripts/extract_format_truth.do` writes
  `test/fixtures/format_truth.json` in `date_truth.json`'s shape (§Stata truth); a test
  in `test_fixtures_are_committed.py`'s reader scan names it; `git add -f`.
- **TR-04.9 Both renderers.** Every new function reachable from `GlyphMapper`,
  `_dash_load_columns`, `_dash_format_kpi_value` or `_format_stata_numeric` is in the
  function copy list; `_DASH_FMT_JS` and any table constant (`_DASH_FMT_CODES`,
  `_DASH_FMT_WIDTHS`, `_DASH_FMT_MONTHS`, `_DASH_FMT_DAYS`) in the constant list.
  `test_statistical_helpers.py::TestTheServedAppCarriesEveryName` and
  `test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads` must pass.
- **TR-04.10 Security.** The format text is user data (`st_varformat` bypasses the `fmt()`
  character gate; a picture carries any character through `!`). It reaches the writer as
  an argument, is parsed by a bounded regex, and never reaches `exec`, `eval`, a JS
  `Function`, HTML or CSS from this section. Widths are bounded before any padding.

## Boundaries

- No number-to-text **site** changes here: not the KPI writers (`_dash_format_kpi_value`,
  `dash_apply_kpis`, `_kpi_callback_config`, `_kpi_js_number_format`, `_parse_fmt`,
  served `_format_kpi`) beyond TR-04.6's guard — section 11; not dropdowns, sliders,
  tooltips, axes, facet titles, the CSV, colorvar labels — section 12.
- `_stata_numeric_pattern`, `_parse_stata_numeric_fmt`, `_format_date_value_standalone`,
  `_datetime_formatter_for`, `_dash_stata_date_text`, `GlyphMapper._mlabel_date_texts`
  and the legacy `dash_numfmt` family stay in place; sections 11/12 retire them.
- `_dash_option_value`, `_dash_dropdown_values`, the dropdown branches of the masks:
  section 17 (X1); this section does not contradict the amendment that a Bokeh `Select`
  carries numeric values.
- `%x`/`%H`/`%L` are refused, not written (PRD §7). `%tC` leap seconds (G7) and extended
  missing values (G12) are out of scope: `.a` rows are recorded in the fixture and
  excluded from the writer's assertion by an explicit filter naming G12.
- No BUGS.md entry lands here: E1, E3 and G6 close in sections 11 and 12, and an open
  entry would fail `test_tracking_documents.py::TestNoOpenEntryBlocksARelease`
  (DISCOVERY amendment to Q4).
- Silent when honoured (Q22): the writer prints nothing; the only new note is BR-04.5's.

## Stata truth

**Script:** `scripts/extract_format_truth.do` (new), modelled on
`scripts/extract_date_truth.do`: every probe writes a pipe-delimited record between `<`
and `>` sentinels (blanks are load-bearing), one trailing `python:` block reads the record
file and writes the JSON, never calls back into Stata, and writes a backtick as `\x60`.

**Output:** `test/fixtures/format_truth.json`, keys:

- `numeric_formats`: `{fmt: {values: [{value, storage: "double"|"float", display,
  display_cmd, rc}]}}` for the formats `%9.0g %10.0g %8.0g %20.15g %10.0gc %12.0gc
  %-12.0gc %9.0f %9.0fc %9.2f %9.2fc %-9.2f %12.2fc %9.3e %9.4f` (date_truth's list) plus
  `%9,2f %9,2fc %8.0gc %09.2f %-9.0g %9.2g %20.0g %12,2gc %10.3e %9.0e %9.4g %16.0g
  %12.0g`, applied to `6165.2567 3.14159 1e7 -0.5 0.1 1234567.5 52313712223 0.000123456
  1e21 . .a` plus the boundary values `0 123456789 -12345678 12345678 1e-7 1.2e-6 5e-7
  1e100 1e-100 1000.03 31415.9265 0.0000029394 20.5 -1234567.891`, each as a double
  (`display %fmt (v)`) and as a float (`display %fmt (float(v))`). About 1,300 rows.
- `date_formats`: `{fmt: {values: [{value, display, display_cmd, rc}]}}` for `%td %tc %tC
  %tw %tm %tq %th %ty %-td %tdCCYY-NN-DD %tdDD/NN/CCYY %tdMonth_DD,_CCYY %tcHH:MM:SS.sss
  %tdJJJ %tdDayname_Day_Da_day_da %tdDAYNAME %tdyy!/nn %tcHh:MM_am %tcHH:MM:SS.ss
  %twCCYY!www %tdq!Qh!H %tdCCYY!c!!x` on `15000 480 160 2000 -120 0 1 -1 2936549 .`
  (every picture on every value; a value outside a kind's range records what Stata
  prints — the bare number). `%tC` only on values before 1972 (G7).
- `confirm`: `{fmt: rc}` from `capture confirm numeric format` for `%21x %16H %16L %8H
  %8L %8s %9,2f %09.0g %9.2ec %tg %tdXYZ %tbsimple %9.2 %`.
- `kpi`: `sysuse auto`: for `mean(price)`, `min(mpg)`, `max(weight)`, `sum(price)`,
  `count(rep78)`, `median(price)`, `p97.5(price)` and, over a generated `%td` variable
  `when = mdy(1,1,2000) + _n` and a `%tm` one `whenm = mofd(when)`, `min(when)`,
  `max(whenm)`, `mean(when)`, `median(whenm)`, and `mean(price) if price > 1e9` (no
  observations): the exact text dash.ado's `kpi_display` rule gives (`: display %fmt
  value`, `strtrim`), for every format in `%9.0g %10.0g %9.2f %9,2fc %12.0fc %8.0gc %9.2e
  %9.3gc %-9.2f %09.2f %td %tdCCYY-NN-DD %tm %tdMonth_DD,_CCYY` and with no format
  (`"`kpi_value'"`, the macro's own text). These are section 11's truth rows.
- `_meta`: Stata version, run date, the command per row (in `display_cmd`).

**Invocation** (CLAUDE.md rule 10; at most three concurrent Stata sessions):

```
mkdir -p /tmp/dash-s04/tmp && cd /tmp/dash-s04 && STATATMP=/tmp/dash-s04/tmp/ \
  arch -arm64 /usr/local/bin/stata-mp -b do \
  /Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/extract_format_truth.do
```

The log lands in `/tmp/dash-s04/extract_format_truth.log`; read it, never relaunch to
check. `STATATMP` carries the trailing slash and is not the log's directory. The fixture
is hidden by `.git/info/exclude` (`*.json`): `git add -f test/fixtures/format_truth.json`.
`test_fixtures_are_committed.py::test_every_fixture_is_named_by_a_test` needs a test that
names the file by its literal path, and `test_every_do_file_is_named_by_another_script_or_test`
needs the script named too (both in `test/test_display_format_writer.py`).

## TDD test stubs

All in **`test/test_display_format_writer.py`** (new, task 04-01) unless noted. Each names
its pre-fix failure.

- Test: `test_the_fixture_is_present_and_large_enough` — `format_truth.json` exists, has
  ≥ 1,000 numeric rows, ≥ 150 date rows, the `confirm` and `kpi` blocks; `pytest.fail`
  (not skip) with "task 04-02 must land first" when absent. Pre-fix: fails (no fixture).
- Test: `TestPythonWriter::test_every_numeric_display_matches_stata_exactly` — every
  numeric row (value not `.a`; `.a` rows counted and excluded with a comment naming G12):
  `_dash_fmt(value, fmt, storage) == display` (padded). Pre-fix: `AttributeError`.
- Test: `TestPythonWriter::test_every_date_display_matches_stata_exactly` — every
  `date_formats` row. Pre-fix: `AttributeError`.
- Test: `TestPythonWriter::test_text_strips_and_missing_is_a_dot` — `_dash_fmt_text(nan,
  "%9.2f") == "."`, `_dash_fmt_text(nan, "%td") == "."`, `_dash_fmt_text(6165.2567,
  "%10.0g") == "6165.257"`.
- Test: `TestPythonWriter::test_a_refused_or_unknown_format_is_written_in_9_0g` —
  `_dash_fmt_text(1.5, "%21x") == _dash_fmt_text(1.5, "%9.0g")`, likewise `"%9.999999999f"`
  and `"bogus"`, each under 1 s and 64 characters (rule 1; mirrors
  `test_adversarial_matrix.py::TestNumericFormatBounds`).
- Test: `TestParser::test_kinds` — parametrised: `%9.2f`→f, `%12.0gc`→g, `%-12.3e`→e,
  `%9,2fc`→f with `comma_dec`, `%09.2f`→f with `zero`, `%td`→t, `%tdCCYY-NN-DD`→t with the
  picture, `%21x`→x, `%16H`→H, `%16L`→H, `%12s`→None, `%9.2`→None, `%2046.2f`→None,
  `%9.30f`→None, a non-ASCII digit format→None.
- Test: `TestParser::test_refusal_messages` — `_dash_fmt_refusal("%21x")` names `%21x` and
  "hexadecimal"; `("%16H")` names IEEE; `("%9.2")` says it is not a display format;
  `("%9.2f")`, `("%tm")` are None.
- Test: `TestStataValueOf::test_each_kind` — 15000 days → ms → `_dash_stata_value_of(ms,
  "td") == 15000.0`; `%tm` 480 (2000m1) from its first day's ms → 480; a mid-month ms
  → 480 (floor); `tq` 160, `th` 80, `ty` 2000, `tw` 2080 (1960w1 + 40 years) and
  2000's last days → week 51 not 52; `tc` 15000 → 15000.0; None/NaN/NaT → None; a value
  past 31dec9999 → None.
- Test: `TestJavaScriptTwin::test_every_fixture_row_matches_under_node` — ONE node run:
  the harness is `_DASH_FMT_JS` + a JSON array of every numeric and date row + a loop
  printing `dash_fmt(value, fmt, storage)`; compare to `display`. Pre-fix: `AttributeError`
  on `dr._DASH_FMT_JS`.
- Test: `TestJavaScriptTwin::test_the_twins_agree_where_the_languages_disagree` — Python
  and node on `1e-7 5e-7 1e-6 1.5e-5 1e-4 1e15 1e16 9999999999999998 1e20 1e21 -0.0`
  under `%9.0g %12.0g %20.0g %9.2f %12,2gc %10.3e` and on `dash_float32_text` vs
  `_dash_float32_text` for `0.1 0.3 1e-7 16777217 3.4e38`.
- Test: `TestJavaScriptTwin::test_stata_value_of_agrees_with_python` — the
  `TestStataValueOf` cases under node.
- Test: `TestJavaScriptTwin::test_years_below_1000_are_not_remapped` — `dash_fmt(-679350,
  "%td")` under node equals `01jan0100` (the fixture's `%td -679350` row from
  `date_truth.json`).
- Test: `TestJavaScriptTwin::test_every_shipped_script_defines_dash_fmt_once` —
  `_FILTER_JS`, `_DASH_CSV_SAVED_JS`, `_DASH_CSV_SERVED_JS` and the brush code a rendered
  page attaches each contain exactly one `function dash_fmt(`; the served app source
  contains `_DASH_FMT_JS = `.
- Test: `TestJavaScriptTwin::test_bounds_under_node` — `dash_fmt(1.5, "%9.999999999f")`,
  `("%1" + "0"*5000 + ".2f")` return in under a second, under 64 characters.
- Test: `TestExport::test_the_writer_sends_storage_types` — `FakeSfi` with `types={"x":
  "float", "y": "double", "s": "str8"}`: the document's `storageTypes` equals it; the key
  set of `test_string_value_export.py:284-287` plus `storageTypes`. (Flips that assertion
  in `test/test_string_value_export.py` in the same task.)
- Test: `TestLoaders::test_both_loaders_carry_g_and_e_formats` — `_dash_load_columns`
  with `{"p": "%8.0gc", "e": "%10.3e", "f": "%9.2f", "d": "%td"}` returns all three numeric
  formats; the served app built from such a spec has `_NUM_FORMATS` with the three and
  `_FORMATS` with all four including a custom picture `%tdCCYY-NN-DD`.
- Test: `TestLoaders::test_a_variables_own_x_format_falls_back_with_one_note` — formats
  `{"h": "%21x"}`: `numeric_formats["h"] == "%9.0g"`, exactly one warning naming `h` and
  `%21x`, in both modes (served: the warnings `_served` captures).
- Test: `TestLoaders::test_storage_types_reach_both_renderers_and_the_mapper` — saved
  `r.storage_types`, `r.mapper.storage_types` (through `_dash_attach_labels`) and the served
  `meta['storage_types']`.
- Test: `TestTheGuard::test_a_card_on_a_g_variable_is_unchanged_until_section_11` —
  `_dash_effective_kpi_fmt({}, "price", {"price": "%8.0gc"}) == "%9.0g"` and with
  `{"price": "%9.2f"}` → `%9.2f` (documents TR-04.6; section 11 inverts it).
- Test: `TestConsumers::test_format_stata_numeric_delegates` — the 56 `date_truth` cases
  still pass through `_format_stata_numeric`; `%9.3e` of 1234.5678 is now `1.23e+03`
  (the fixture row); NaN is still `""`.
- Test: `TestDashAdo::test_the_ado_refuses_what_the_renderer_refuses` — reads dash.ado's
  format branch text, extracts the `[xHL]` regex, and asserts it matches every fixture
  `confirm` format whose `_dash_fmt_refusal` is not None and rc 0 (`%21x %16H %16L %8H
  %8L`) and none whose kind is f/g/e/t.
- Test: `test_fixture_and_script_are_named` — literal
  `test/fixtures/format_truth.json` and `scripts/extract_format_truth.do` (for
  `test_fixtures_are_committed.py`).
- cscript **`test/test_option_validation.cscript`** (task 04-08): OV-121 `fmt(%21x)` rc
  198 naming fmt() and %21x; OV-122 `fmt(%16H)` rc 198; OV-123 `fmt(%16L)` rc 198; OV-124
  `fmt(%9,2fc)` rc 0; OV-125 `fmt(%tm)` rc 0; OV-126 `fmt(%10.0g)` rc 0.

**Mutation table** (apply, see the named test fail, revert):

| break this | test that must die |
|---|---|
| in the `%w.0g` writer use `w-1` significant digits | `test_every_numeric_display_matches_stata_exactly` (`%9.0g` 1234567.891) |
| write positives in `w` columns instead of `w-1` | the same, on `%9.3e` 1234.5678 and `%9.0f` 123456789 |
| JS: `new Date(y, m, d)` instead of `setUTCFullYear` | `test_years_below_1000_are_not_remapped` |
| JS: fall back to `String(v)` for `%g` | `test_the_twins_agree_where_the_languages_disagree` |
| drop `_DASH_FMT_JS` from the constant copy list | `test_every_shipped_script_defines_dash_fmt_once` (served) |
| remove the `[xHL]` refusal from dash.ado | OV-121 and `test_the_ado_refuses_what_the_renderer_refuses` |
| skip the width bound in `_dash_fmt_parse` | `test_a_refused_or_unknown_format_is_written_in_9_0g` (time/length) |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Python writer equals Stata, numeric and date, padding included | pytest | format_truth.json | n/a (module) |
| JS twin equals Stata and equals Python | node (one process per test) | format_truth.json | n/a |
| Twin agreement on the language-disagreement ranges | pytest + node | none | n/a |
| Parser kinds, refusals, bounds, timing | pytest + node | value_truth.json (confirm), format_truth.json `confirm` | n/a |
| Export carries storageTypes; FakeSfi | pytest | none | n/a |
| Loaders carry g/e and the full map; `%x` fallback with one note | pytest | none | yes |
| Every shipped script holds `dash_fmt` once; served copy lists | pytest | none | yes |
| `dash kpi fmt(%21x)` r(198) | cscript OV-121..126 | none | n/a |
| dash.ado regex = renderer refusal set | pytest reading dash.ado | format_truth.json | n/a |
| The 56 existing f/fc cases still pass through the wrapper | pytest | date_truth.json | n/a |

Acceptance criteria:

- **AC-04.1** `python3 -m pytest test/test_display_format_writer.py -q` passes with zero
  skips under both interpreters (`make test` and `make test-dev`), and the numeric row
  count it asserts is ≥ 1,000.
- **AC-04.2** `node` runs `_DASH_FMT_JS` over every fixture row with no exception and no
  mismatch.
- **AC-04.3** `test_option_validation.cscript` passes OV-121..126; `run_all_cscripts.do`
  reports it PASS.
- **AC-04.4** The full pytest suite is green with the flipped tests named in the commit
  messages; `TestTheServedAppCarriesEveryName` and
  `TestTheServedAppDefinesEveryNameItReads` pass.
- **AC-04.5** `git diff --stat main -- dash_render.py` shows changes confined to the
  regions this section names; no number-to-text site of sections 11/12 is edited.

## Tasks

<task type="auto" id="04-01">
  <name>Write the failing tests for the writer, twin, export, loaders and refusal</name>
  <files>test/test_display_format_writer.py (new)</files>
  <action>
    Create `test/test_display_format_writer.py` with the header block of
    `test/test_statistical_helpers.py` (paths, `import dash_render as dr`), a node runner
    modelled on `test/test_export.py:41-53` `_run_js` (temporary `.mjs`, `subprocess.run`,
    JSON on stdout; `pytest.skip` only when node is absent, and a module-level assertion
    in `TestJavaScriptTwin` that at least one twin test ran), and `_fixture()` that loads
    `test/fixtures/format_truth.json` and `pytest.fail`s with "task 04-02 must land first:
    test/fixtures/format_truth.json is missing" when absent. Write every test named in
    "TDD test stubs" with exactly those names, including the `test_fixture_and_script_are_named`
    test whose body holds the literal paths. For the JS fixture test, hand node ONE JSON
    array of every row and read back one array, so the whole fixture costs one process.
    Do not touch dash_render.py, dash.ado or any fixture in this task. Run the file
    against the unmodified tree and paste the failure summary (the fixture-missing
    failures and the `AttributeError: module 'dash_render' has no attribute '_dash_fmt'`
    failures) into the commit message. Commit on `s3-bugs`; no AI references.
  </action>
  <verify><![CDATA[`cd /Users/billy/Desktop/Programs/StataPrograms/d/dash && python3 -m pytest test/test_display_format_writer.py -q 2>&1 | tail -5` reports 0 passed, no collection error, and the failures are fixture-missing or AttributeError, never a skip.]]></verify>
  <done>Every regression test of this section exists, collects cleanly and fails against 91d97be for the recorded reason; nothing else changed.</done>
</task>

<task type="auto" id="04-02">
  <name>Record Stata's display truth into format_truth.json</name>
  <files>scripts/extract_format_truth.do (new), test/fixtures/format_truth.json (new)</files>
  <action>
    Write `scripts/extract_format_truth.do` following `scripts/extract_date_truth.do`'s
    structure: a header naming the run command, a record file under `c(tmpdir)`, and
    for each block in §Stata truth a `foreach` over formats and values writing
    `NVAL|fmt|value|storage|rc|DISPLAY|display_cmd` (numeric, once per storage: the
    double through `display %fmt (v)` and the float through `display %fmt (float(v))`),
    `DVAL|fmt|value|rc|DISPLAY|cmd`, `CONF|fmt|rc`, and `KPI|stat|var|fmt|DISPLAY`
    computed exactly as dash.ado:6325-6335 computes `kpi_display` (`quietly summarize`,
    then `: display %fmt value`, `strtrim`; with no format the macro's own text). Capture
    every DISPLAY between the less-than and greater-than sentinel characters, exactly as
    `extract_date_truth.do:120-121` does, so blanks survive. One trailing `python:` block reads the records, unwraps
    the sentinels, writes `test/fixtures/format_truth.json` with `json.dump(indent=2,
    sort_keys=True)`, never calls Stata, and writes any backtick as `\x60`. Run it with the
    §Stata truth command line; read `/tmp/dash-s04/extract_format_truth.log` to the end
    (do not relaunch). `git add -f test/fixtures/format_truth.json`. Record in the commit
    message the row counts the script printed.
  </action>
  <verify>`python3 -c "import json;d=json.load(open('test/fixtures/format_truth.json'));print(sum(len(v['values']) for v in d['numeric_formats'].values()), sum(len(v['values']) for v in d['date_formats'].values()), d['confirm']['%21x'], d['confirm']['%16H'], len(d['kpi']))"` prints a numeric count of at least 1000, a date count of at least 150, `0 0` and a KPI count of at least 100; `python3 -m pytest test/test_display_format_writer.py -q -k "fixture_is_present or fixture_and_script"` passes; `git ls-files test/fixtures/format_truth.json` lists it.</verify>
  <done>Stata's own display text for every format and value this section names is committed, with the command that produced each row, and the fixture is tracked and named by a test.</done>
</task>

<task type="auto" id="04-03">
  <name>Implement the Python numeric writer and parser</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    In dash_render.py, in the "One implementation, two callers" region (after
    `_dash_stata_date_text`, :15618-15645), add `_dash_fmt_parse`, `_dash_fmt_kind`,
    `_dash_fmt_refusal`, `_dash_float32_text`, `_dash_fmt_number`, `_dash_fmt` and
    `_dash_fmt_text` as TR-04.1 and TR-04.2 specify (dates raise nothing yet: `_dash_fmt`
    routes kind "t" to `_dash_fmt_date`, added in 04-04, so leave a one-line stub that
    returns the padded number until then). Before writing the `%g` branch, print the
    fixture's rows for `%12.0g` and `%20.0g` of 0.1 as float and as double and choose the
    `storage="float"` rule the rows demand; record the choice in `_dash_fmt`'s docstring
    with the two display strings. Keep WP-20's bounds in `_dash_fmt_parse`. Add each new
    function to `test/function_test_map.py` naming the test from this section that
    exercises it (`_dash_fmt` → `TestPythonWriter::test_every_numeric_display_matches_stata_exactly`,
    `_dash_fmt_parse` → `TestParser::test_kinds`, and so on). Iterate against the fixture
    until every numeric row passes; where a row contradicts the derived rule, follow the
    row and note the case in the docstring.
  </action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "TestPythonWriter and numeric or TestParser or refused_or_unknown"` passes; `python3 -c "import dash_render as d;print(repr(d._dash_fmt(6165.2567,'%10.0g')), repr(d._dash_fmt(1000.03,'%9,2fc')), repr(d._dash_fmt(float('nan'),'%9.2f')))"` prints `'  6165.257' ' 1.000,03' '        .'`; `python3 -m pytest test/test_function_test_map.py -q` passes.</verify>
  <done>The Python numeric writer reproduces every numeric fixture row, padding included, and the parser refuses what Stata refuses within WP-20's bounds.</done>
</task>

<task type="auto" id="04-04">
  <name>Implement the Python date writer and the Stata-value recovery</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action>
    Add the module constants `_DASH_FMT_CODES` (the ordered code table of TR-04.3),
    `_DASH_FMT_MONTHS`, `_DASH_FMT_DAYS` and `_DASH_FMT_WIDTHS` (each code's maximum
    width), then `_dash_fmt_calendar(value, tkind)`, `_dash_fmt_date(parsed, value)` and
    `_dash_stata_value_of(column_value, date_kind)` as TR-04.1/TR-04.3 specify, and route
    `_dash_fmt`'s kind "t" to `_dash_fmt_date`. The calendar of a period value is the
    period's first day; a `%tc` time truncates; a value outside Stata's range prints the
    bare number as Stata does (`display %td 2936550` prints 2936550). Right-align to the
    picture's maximum width, left-align for `%-t`. Reuse `_dash_unix_ms_to_unit` for the
    period kinds in `_dash_stata_value_of` and floor it. Map the new names in
    `test/function_test_map.py`. Iterate against the `date_formats` rows.
  </action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "TestPythonWriter or TestStataValueOf"` passes; `python3 -c "import dash_render as d;print(repr(d._dash_fmt(480,'%tm')), repr(d._dash_fmt(15000,'%tdMonth_DD,_CCYY')), d._dash_stata_value_of(978393600000,'td'))"` prints `' 2000m1'`, the fixture's text for that picture, and `15341.0`.</verify>
  <done>The Python writer reproduces every date fixture row and recovers a Stata date value from epoch milliseconds for all eight kinds.</done>
</task>

<task type="auto" id="04-05">
  <name>Write the JavaScript twin and thread it into every shipped script</name>
  <files>dash_render.py</files>
  <action>
    Add the string constant `_DASH_FMT_JS` immediately before `_DASH_CSV_JS` (:14012),
    defining `dash_fmt_parse`, `dash_fmt_kind`, `dash_float32_text`, `dash_fmt`,
    `dash_fmt_text`, `dash_stata_value_of` and `dash_html_escape`, as a line-for-line
    transliteration of the Python functions (same code table, same widths table, same
    rounding, same branch order; comments naming the Python original). Use UTC `Date`
    with `setUTCFullYear` for calendars; clamp `toFixed`/`toPrecision` arguments to 0..100
    and widths to 2045; never `String(v)`, `Intl` or `toLocaleString` for a formatted
    value. Prepend it exactly once: `_DASH_FILTER_MASK_JS = _DASH_FMT_JS + """…"""`,
    `_DASH_CSV_SERVED_JS = _DASH_FMT_JS + _DASH_CSV_JS + """…"""`, and at the brush wiring
    (:23483-23496) `code=_DASH_FMT_JS + _pctl + _helpers + _BRUSH_JS`. Add
    `"_DASH_FMT_JS"` and the four table constants to the constant copy list beside
    `_DASH_CSV_SERVED_JS` (:24408). Do not change `_FILTER_JS`'s body or the KPI writers.
  </action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k TestJavaScriptTwin` passes (every fixture row under node, the disagreement ranges, years below 1000, exactly one `function dash_fmt(` per shipped script, bounds); `python3 -m pytest test/test_statistical_helpers.py -q -k "TestFilterJavaScript or CarriesEveryName"` and `test/test_export.py -q` still pass.</verify>
  <done>Every page script and the served app carry one JavaScript writer whose output equals the Python writer's on every fixture row.</done>
</task>

<task type="auto" id="04-06">
  <name>Export storage types and carry them and the full format map into both renderers</name>
  <files>dash_render.py, test/test_string_value_export.py, test/function_test_map.py</files>
  <action>
    In `_dash_write_stata_data` (:1280-1290, :1360-1368) read `data.getVarType(v)` for
    every variable into `storage_types` and write it as `"storageTypes"` in the document;
    give `FakeSfi.Data` a `getVarType(v)` returning `fake.types[v]` and flip the key-set
    assertion at `test_string_value_export.py:284-287` to include `storageTypes`. In the
    saved `_load_data` (:21160-21187) read `stata_json.get("storageTypes", {})` into
    `self.storage_types` and pop qualifier columns from it as formats are popped; in the
    served loader (:25734-25756) read the same into `meta['storage_types']`; in the builder
    emit `"_FORMATS = %r" % (full bo['formats'] map)` beside `_NUM_FORMATS` (:24930) and
    in `make_document` (:25860-25877) bind `_storage_types = meta.get('storage_types', {})`.
    Extend `_dash_attach_labels` (:18745) with `storage_types=None` →
    `mapper.storage_types`, and pass it from both callers (saved: where the mapper is
    attached in `_load_data`/`_build_figures`; served: :25877). Map any new nested function
    in `test/function_test_map.py`.
  </action>
  <verify>`python3 -m pytest test/test_display_format_writer.py -q -k "TestExport or storage_types_reach"` and `python3 -m pytest test/test_string_value_export.py -q` pass; `grep -n "_FORMATS = %r\|_storage_types = " dash_render.py` shows both served lines.</verify>
  <done>Each variable's storage type travels from Stata into both renderers and the mapper, and the served app holds the full display-format map including custom pictures.</done>
</task>

<task type="auto" id="04-07">
  <name>Widen the loaders, wrap the old writer, guard the card, and flip what moves</name>
  <files>dash_render.py, test/function_test_map.py, test/test_served_dates.py</files>
  <action>
    In `_dash_load_columns` (:672-673) keep a format when `_dash_fmt_kind(fmt) in ("f",
    "g", "e")`; when `_dash_fmt_refusal(fmt)` is not None and the format is not a date,
    `_dash_warn_once(("format", col), f"dash: variable '{col}' has display format
    {fmt!r}, which the dashboard cannot write; it is shown in %9.0g.")` and store
    `"%9.0g"`. Use the same predicate in `_NUM_FORMATS` (:24930-24934). Make
    `_format_stata_numeric` the TR-04.6 wrapper (docstring: what it delegates and why its
    `""` contract stays). Add TR-04.6's guard to `_dash_effective_kpi_fmt` with the
    "section 11 removes this guard" comment. Add every new function to the served function
    copy list (:24466-24687) and make `test/function_test_map.py` current. Add a `%g` case
    to `test_served_dates.py::TestOneColumnReader::test_the_reader_converts_dates_and_numbers`.
    Run the full suite once (`python3 -m pytest test/ -q`); flip only assertions on marker
    labels of a variable carrying a `%g`/`%e` format in its spec, or on `%w.de` text,
    citing this section in a comment; list each flipped assertion in the commit message
    with old and new text. Never weaken the writer to keep an old assertion green.
  </action>
  <verify><![CDATA[`python3 -m pytest test/test_display_format_writer.py -q` passes entirely; `python3 -m pytest test/ -q 2>&1 | tail -3` reports no failures and no new skips; `python3 -m pytest test/test_resource_limits.py -q -k DefinesEveryName` and `test/test_help_claims_4.py -q -k KeepsItsFormat` pass.]]></verify>
  <done>Both loaders carry every writable format, a refused variable format falls back with one note, `_format_stata_numeric` writes Stata's text through the new writer, cards are unchanged pending section 11, and the full suite is green with every flipped assertion recorded.</done>
</task>

<task type="auto" id="04-08">
  <name>Refuse %x and %H formats in dash kpi fmt() with r(198)</name>
  <files>dash.ado, test/test_option_validation.cscript, test/test_display_format_writer.py</files>
  <action><![CDATA[
    In dash.ado's format branch (:2294-2313), after `confirm numeric format` sets `ok`,
    add the TR-04.7 check: `if `ok' & regexm(scalar(`V'), "^%-?[0-9]*[xHL]$")` then
    `_dash_say("err", …)` naming the format through Mata by value and `exit 198`. Update
    the comment block at :2298-2304 to say `%21x` and `%16H` are now refused after
    `confirm`. In `test/test_option_validation.cscript` add OV-121..OV-126 with `_ov_case`
    as :685-686 do, updating the header list at :150-156. Make
    `TestDashAdo::test_the_ado_refuses_what_the_renderer_refuses` read the regex from
    dash.ado's text (as other tests read dash.ado) rather than from a copy. Run the
    cscript from a scratch directory: `mkdir -p /tmp/dash-s04b/tmp && cd
    /Users/billy/Desktop/Programs/StataPrograms/d/dash/test && STATATMP=/tmp/dash-s04b/tmp/
    arch -arm64 /usr/local/bin/stata-mp -b do test_option_validation.cscript`; read the
    log; confirm `c(python_exec)` is still set if anything skipped.
  ]]></action>
  <verify>The cscript log ends in its ALL CHECKS PASSED line with OV-121..126 PASS; `python3 -m pytest test/test_display_format_writer.py -q -k TestDashAdo` passes; `python3 -m pytest test/test_cscript_hygiene.py -q` passes.</verify>
  <done>`dash kpi …, fmt(%21x)`, `fmt(%16H)` and `fmt(%16L)` stop with r(198) naming the format, every other accepted format still registers, and the Stata and renderer refusal sets are asserted equal.</done>
</task>

<task type="auto" id="04-09">
  <name>Document the writer and the refusal</name>
  <files>dash.sthlp, CHANGELOG.md, test/test_display_format_writer.py</files>
  <action>
    In dash.sthlp's `fmt()` row (:1259-1261) say a numeric or date display format —
    `%w.df`, `%w.dg`, `%w.de`, each with `c`, the comma decimal, and any `%t` picture — and
    that `%x`, `%H` and `%L` are refused with r(198) (the card is written by the page, which
    cannot write a hexadecimal or IEEE dump); do not yet claim the card honours them (that
    is section 11's edit). Add to CHANGELOG.md under the current release: "New" — the
    Stata display-format writer shared by the saved page and the served app, pinned to
    `format_truth.json`; the export's storage types; "Changed behaviour" — `fmt(%21x)` and
    `fmt(%16H)` are refused with r(198), a variable's own such format draws in `%9.0g` with
    one note; "Results that change" — marker labels of a variable with a `%g`/`%e` display
    format now read as Stata writes them (give one before/after: a float 0.1 labelled
    `0.10000000149011612`, now `.1`), and `mlabformat(%9.3e)` of 1234.5678 reads
    `1.23e+03`, not `1.235e+03`. Add a help-claim test in `test_display_format_writer.py`
    that the `fmt()` paragraph names r(198) and `%21x`. No BUGS.md entry (see Boundaries);
    no AI references.
  </action>
  <verify>`grep -n "21x" dash.sthlp CHANGELOG.md` shows both; `python3 -m pytest test/test_display_format_writer.py test/test_tracking_documents.py -q` passes; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0.</verify>
  <done>The help and the changelog describe what this section changed for the user, and no open BUGS.md entry exists for it.</done>
</task>

## Section completion criteria

- `test/fixtures/format_truth.json` is committed with ≥ 1,000 numeric and ≥ 150 date
  rows, each carrying the Stata command that produced it; `extract_format_truth.do` is
  named by a test.
- `_dash_fmt`, `_dash_fmt_text`, `_dash_fmt_kind`, `_dash_fmt_refusal`,
  `_dash_stata_value_of` and `_DASH_FMT_JS` exist with the signatures in TR-04.1/TR-04.4,
  every fixture row passes in Python and under node, and every new name is in the copy
  lists and `function_test_map.py`.
- `storageTypes` is exported and read by both loaders; `_FORMATS` (full) and
  `_NUM_FORMATS` (f/g/e) exist in the served app; a refused variable format falls back
  with one note.
- `dash kpi fmt(%21x)` is r(198) in the cscript and the regex parity test passes.
- The full pytest suite and `test_option_validation.cscript` are green with no skips; every
  flipped assertion is named in a commit message; CHANGELOG and dash.sthlp carry the
  section's user-visible changes; sections 11 and 12 can begin.

## Notes

- **The fixture is the arbiter.** The `%w.0g` rule in §Evidence is a hypothesis
  consistent with every documented and measured example; where a fixture row disagrees,
  the row wins and the docstring records the case. Never "fix" a fixture row.
- **The sign column.** `date_truth.json` already shows it (`%9.3e` 1234.5678 →
  ` 1.23e+03`, `%9.0g` 1234567.891 → `  1234568`). The current `_format_stata_numeric`
  tests `len(plain) <= width`; the new fixture's `123456789` under `%9.0f` decides whether
  positives get `w` or `w-1` columns.
- **Stata's rounding.** `dash_tie_even` (14388) documents that the old JS rounded ties up
  where Python rounded to even; the fixture's `20.5`/`1234567.5` rows pin Stata's own
  behaviour, which both new twins follow — Python must not use `round()` or `format()`
  for the digits.
- **Padding survives only in `_dash_fmt`.** Every page site uses `_dash_fmt_text`; the
  padded form exists so the fixture can be compared exactly and so section 11's cert test
  can compare `strtrim`med `kpi_display` to `_dash_fmt_text`.
- **Years below 1000 in JavaScript.** `new Date(100, 0, 1)` is 2000-01-01 in some engines
  and 0100 in others; `Date.UTC(100, …)` remaps 0-99 only. Use `setUTCFullYear` on a
  zero Date every time. `date_truth.json`'s `%td -679350` row (01jan0100) pins it.
- **Copy lists.** A table constant read by a copied function must be in the constant
  list, or the served page raises `NameError` at draw time. The guards named in TR-04.9
  catch a miss only if the served spec exercises the path; run them and also grep the
  generated app for each new name.
- **`_dash_warn_once` keys** are per render (`_DASH_NOTED` is cleared per build); the
  served app copies `_dash_warn_once` already.
- **Do not add `_DASH_FMT_JS` to `_DASH_CSV_JS`.** `_DASH_CSV_SAVED_JS` is
  `_DASH_FILTER_MASK_JS + _DASH_CSV_JS + …` and would define `dash_fmt` twice.
- **Line numbers drift** by the size of each insertion; every anchor above is also a
  symbol, and the symbol is authoritative.
- **Stata sessions.** One run for 04-02 and one for 04-08; if a cscript SKIPs where it
  passed before, check `c(python_exec)` before trusting it (many concurrent sessions can
  drop it from `~/.stata19/console/stata19.rc`; restore with `set python_exec
  /opt/anaconda3/bin/python3, permanently`).
- **Hand-off to S11/S12.** They call `_dash_fmt_text(value, fmt, storage)` with the Stata
  value, `_dash_stata_value_of(ms, kind)` for dates, `self.formats`/`_FORMATS` for the
  full format, `self.storage_types`/`meta['storage_types']` for storage; the JS side
  calls `dash_fmt_text(v, fmt, storage)` and `dash_stata_value_of(ms, kind)`; a
  `CustomJSTickFormatter`/`CustomJSHover` code string is `_DASH_FMT_JS + "return …"` with
  the format carried in `args`.
