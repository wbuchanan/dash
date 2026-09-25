# Section 11: KPI cards

> Part of: WP-28 · Gaps: E1 (+ E3, G6 on cards) · Risk: yellow · Batch: 3 · Depends on: 04, 17 · Blocks: 19 · Tasks: 7, 1 commit (E1)


## Review amendments (Phase 4, 2026-09-25) — binding; they override any conflicting text below

> Batch **3** · Depends on **04, 17** · Blocks **19** · Risk **yellow** · Commits: one commit (E1) → CHANGELOG `Results that change`

- D4: this section follows S17: `dash_apply_kpis` is adapted to S17's per-group call, and the brush slice marker `dash_apply_kpis(new_data,` (dash_render.py:14650, 23485 at 91d97be; S17's comment line after batch 2) must keep working — 11-03 rewrites only the body of `function dash_apply_kpis(` and a test pins the marker order.
- D11: KF-01..KF-05 are a block of the one truth script `test/test_gaps2_truth.cscript` (11-06); no new cscript, no runner edit, no hygiene-pin edit.

Applies to every section:
- D1 (binding): tasks are work steps; commits are per gap (S01-S04: one each). The failing regression tests are written first and run against the unmodified tree; their output at 91d97be is recorded in the fix commit's message (Q24) and they are committed together with the fix, never alone (CLAUDE.md rule 4).
- D3 (binding): each gap's BUGS.md entry is appended at the END of BUGS.md in the closed form with `- Resolution: Fixed <ddmonyyyy> (WP-28, <ID>). <what changed>. Pinned by test/<file>::<Class>::<test>.`
- D2 (binding): each closing task replaces the gap's `<!-- WP-28 <ID> -->` marker(s) that S01 placed in the CHANGELOG list named above; it does not add a new line elsewhere.
- D6 (binding): every Stata run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (see `index.md` step 0); no section launches the full cert suite or the release gate.
- D5 (binding): shared files follow merge rules R1-R6 in `index.md` (cscript registration and hygiene pins, copy lists and maps, help/CHANGELOG/BUGS.md, graph-key lists, fixtures, parity corpus).
- D7: XML fields holding `&`, `<` or `>` are CDATA-wrapped (done mechanically); task names over 8 words are shortened and `done` fields put in the past tense during the detailed fixer pass.

Detailed edits from `../review/consistency.md`, `../review/requirements-security.md` and `../review/feasibility.md` (as adjusted by `../review/DECISIONS.md`) were applied to this file in the fixer pass (2026-09-25); the text below conforms to this block.

## Overview

A KPI card is the one place dash promises a format by name: `dash kpi …, fmt(%fmt)`
(dash.sthlp:1259-1261). GAPS2 E1 measured that the card does not keep the promise:
"`fmt(%10.0g)` of 6165.2567 shows `6e+03` in both modes and after every move. `%9,2f`,
`%21x` and `%16H` show the raw value. `%td` of 15000 shows `15000.0`. Date KPIs ignore
`fmt()`. Without `fmt()` a variable's own %g format is dropped, so the card shows 6165.26
where `summarize` prints 6165.257." Report B adds: a missing date on a card reads `""` at
first paint and `—` after a move where Stata shows `.` (DISCOVERY Q13), and the
JavaScript card rebuild concatenates its text into HTML without escaping (report B §1.4,
security).

After this section, every card — first paint, after a filter move, after a brush, saved
and served — shows the text Stata's `display` gives for the card's effective format:
`fmt()` if given, else the variable's own display format (a `%t` picture for a date-valued
statistic of a date variable), else `%9.0g`. Numbers, dates and missing values go through
section 04's `_dash_fmt_text` and its JavaScript twin `dash_fmt_text`, the legacy
`dash_numfmt` family and the fixed date pictures are retired, and the rebuilt card escapes
its text. E3 and G6 are closed here for cards only; their other sites are section 12.

Why one section: report B §1.3 rows 1-3 are one code path with three entry points
(`_build_kpi_html`, `dash_apply_kpis`, `_on_filter_change`/the brush handlers) that must
agree or the card changes shape on the first interaction — the invariant
`test_help_claims_4.py::TestACardKeepsItsFormatWhenAFilterMoves` already pins.

**Test order (CLAUDE.md rule 7) and commit rule (D1): task 11-01 writes every regression
test for this section**, runs it against the tree as batch 2 leaves it (sections 04 and 17
merged) and saves the failure text to `<scratch>/11-01-failure.txt` -- it does not commit
(a red tree is never committed, rule 4); 11-02 and 11-03 turn the sites green; 11-04 and
11-05 flip the pinned tests; 11-06 appends the certification block; 11-07 closes the entry
and makes the section's ONE commit (E1), subject ending `(GAPS2 E1)`, whose body opens with
the saved failure text (Q24; S01 TR-01.9). The failing tests land in that commit, never
alone.

## Risk: [yellow] — three writers in two languages must agree with Stata and with each other on every card, and one of them builds HTML by string concatenation

**Why.** The card is rewritten by Python at first paint and by JavaScript after every move
on the saved page; a difference is a card that flickers to a new value the moment the user
touches a widget. The JavaScript rebuild is an HTML sink.

**Risk factors.** (1) The JS config fields change (`numfmt`, `decimals`, `commas`,
`general` retired), and three tests plus the brush wiring slice `_FILTER_JS` by comment
markers — on a tree where section 17 has already replaced the single `dash_apply_kpis`
call with a per-group loop. (2) A `%t` picture can carry the user's own text through `!`,
which now reaches the JS rebuild. (3) A date KPI's value is epoch milliseconds in both
modes and must be converted back before formatting. (4) The variable's own format is now
consulted for every statistic, which is wrong for a count of a date variable.

**Mitigation.** (1) Section 04's `_DASH_FMT_JS` is the only writer; only the body of
`function dash_apply_kpis(` is rewritten, section 17's loop and its marker comment are left
as they are, the slice markers are updated deliberately in the tests that use them, a test
pins the marker order, and the format-keeping invariant test is extended, not weakened.
(2) `dash_html_escape` (section 04) wraps the text in the rebuild, and a test injects `!<`
into a picture. (3) `_dash_stata_value_of` (section 04) in both twins; the fixture's `kpi`
block holds Stata's text for date statistics. (4) The effective format rule is written
once with the statistic in hand and pinned by Stata's strings for `count(when)`.

## Dependencies

- Depends on: section 04 (`_dash_fmt_text`, `_dash_stata_value_of`, `_DASH_FMT_JS`,
  `dash_html_escape`, `self.formats`/`_FORMATS`, `storage_types` and the served
  `_storage_types` bound in `make_document`, the `kpi` block of `format_truth.json`, and
  the guard in `_dash_effective_kpi_fmt` this section removes); section 17 (`kpi_config`
  entries carry `"use"`, the per-group loop that calls
  `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)` once per exclusion group,
  and the comment line `// dash_apply_kpis(new_data, ...) runs once per exclusion group
  below` that keeps the brush-wiring marker). Section 03's `test/js_runner.py` (batch 1)
  is on the tree: one move suffices here, so the after-move tests may use `hc4._run_js` or
  `js_runner.JsSession`.
- Blocks: section 19 (closeout).
- Parallel batch: 3. Can run with: 12, 15, 18. Merge order inside batch 3: S18, S15, S11,
  S12 (index.md); S12 merges after this section and edits no function this section edits
  (`_format_date_value_standalone` and `_dash_stata_date_text` are left to it).
- Why (D4 ordering): S17 (batch 2) rewrote `_FILTER_JS`'s KPI call site into the
  per-group loop and gave `kpi_config` its `use` list; this section rewrites the body of
  `dash_apply_kpis` on that tree, keeps the marker, and adds `fmt`/`storage` beside `use`
  in the config.

## Evidence

### First paint, Python

`_dash_effective_kpi_fmt`, dash_render.py:19591-19606 (with section 04's temporary guard):

```python
19600    explicit = str(kpi.get("fmt", "") or "").strip()
19601    if explicit:
19602        return explicit
19603    own = (numeric_formats or {}).get(varname, "") or ""
19604    if own:
19605        return own
19606    return "%9.0g"
```

`_dash_format_kpi_value`, :19609-19680 — the date branch comes first (so a date KPI ignores
`fmt()`), `%9.0g` and `""` map to Python's `:g` (six significant digits where Stata shows
seven), any other format goes to Python `format()` and a format Python cannot apply falls
back to `str(value)`:

```python
19644    kind = (date_vars or {}).get(varname)
19645    if (kind and date_formatter is not None
19646            and _dash_kpi_date_valued(stat)):
19647        return date_formatter(float(value), kind)
...
19656    if fmt in ("", "%9.0g"):
...
19660        return f"{float(value):g}"
...
19677    try:
19678        formatted = f"{value:{fmt}}"
19679    except (ValueError, TypeError):
19680        formatted = str(value)
```

Measured (report B §1.1): `%10.0g` of 6165.2567 gives `6e+03`, `%9,2f` gives `6165.2567`,
`%td` of 15000 gives `15000`. The renderer's `_format_kpi_value` (:21354) and
`_build_kpi_html` (:23374) call it with `self._effective_kpi_fmt(kpi, varname)`; the
served `_format_kpi` (:25789-25803) calls the same pair with `_NUM_FORMATS` and
`_format_date_value_standalone`, and `_on_filter_change` (:26944-26963) and the brush
handler (:27030-27050) call `_format_kpi`.

### After a move and after a brush, JavaScript

`_kpi_callback_config`, :23385-23451, builds one config per card; the fields the writer
reads are `decimals`, `commas` (from `_parse_fmt`, :22996, dead once `numfmt` is set),
`general`, `numfmt` (from `_kpi_js_number_format`, :23004-23042, kind `f`/`e`/`g`/`str`)
and `datekind` (set only for a date-valued statistic of a date variable); section 17 adds
`use` (the per-target list). `dash_apply_kpis`, :14484-14648: the date branch
(:14578-14604) has fixed pictures and `'—'` for a missing date; the number branch
(:14605-14625) has `'.'` for a missing number, `dash_numfmt` (the only caller of the
:14378-14482 family), then dead `k.general`/`toFixed` branches; the rebuild (:14637-14645)
concatenates `fmt` (the card's text) raw:

```js
14643            '<div id="kpi_val_' + k.name_html + '" style="font-size:36px; font-weight:bold; color:' + k.color + ';">' + fmt + '</div>' +
```

while the Python card escapes it (`_dash_kpi_card_html`, :13629: `_v =
html.escape(str(value))`). `_BRUSH_JS` (:14935) reuses `dash_apply_kpis` through the
slices assembled at :23478-23496 (`// ---- KPI recompute, shared by` …
`dash_apply_kpis(new_data,`, plus `function dash_pctl(` … `// Stata's kernels`), and
`test/test_kpi_brush.py:251` slices up to the FIRST `dash_apply_kpis(new_data,` too. At
91d97be that marker is the single call `dash_apply_kpis(new_data, kpi_config, kpi_divs,
ROW_ID);` at :14650; after section 17 (batch 2) that line reads
`// dash_apply_kpis(new_data, ...) runs once per exclusion group below` and the loop below
it calls `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)` once per exclusion
group, so the slice still ends at a line that follows the whole function body. This
section leaves that line and the loop as they are.

### Stata's own card text

dash.ado:6331-6335 and :6353, :6389, :6974:

```stata
6331    local kpi_display = "`kpi_value'"
6332    if `_fmlen' > 0 {
6333        local kpi_display : display `fmt' `kpi_value'
6334        local kpi_display = strtrim("`kpi_display'")
6335    }
```

So Stata's `kpi_display` equals the card only when `fmt()` was given; without one it is the
macro's own text of the statistic. dash's documented rule for that case is the variable's
own format (`_dash_effective_kpi_fmt`'s docstring; dash.sthlp:1242-1250 for dates), and
the truth for it is `: display %<own format> value`, which section 04's fixture records in
its `kpi` block for each statistic, variable and format, together with the statistic's
value. `count(when)` of a `%td` variable is a count, not a date: Stata's `summarize`
prints it in `%9.0g`, and so does the fixture row.

### Tests that pin today's behaviour (flip, never delete)

- `test/test_date_range.py::…::test_a_kpi_reads_the_placeholder_as_its_date` (:542-545):
  `"31 Dec 9999"`, `"02 Jan 2001"` → `31dec9999`, `02jan2001`.
- `test/test_date_range.py::…::test_the_page_callback_writes_a_kpi_year_in_four_digits`
  (:995-1012): slices `"        let fmt;\n        if (k.datekind) {"` and expects `"01 Jan
  0100"`, `"Jan 0100"`, `"01 Jan 0100 00:00:00"` → the slice moves to `let text;` with
  `_DASH_FMT_JS` prepended and expects `01jan0100`, `0100m1`, `01jan0100 00:00:00`.
- `test/test_server_layer_defects.py::TestTheKpiFormatHelpers::test_a_date_valued_statistic_is_shown_as_a_date`
  (:1100-1106) passes a `date_formatter` lambda → the parameter is retired; the test passes
  `date_vars` and a format and expects Stata's text. `::test_the_default_shows_six_significant_digits`
  (:1088; `21.2973` for 21.297297297 under `%9.0g`) stays: Stata's `%9.0g` gives the same
  seven-significant-digit text here. `::test_an_unusable_format_does_not_raise` (:1097)
  stays (`%notaformat` writes in `%9.0g`).
- `test/test_kpi_values.py::TestKpisUnderFiltering::_js_format` (:421-455) slices `"// ----
  A number written as the card's"` … `"function dash_apply_kpis("` and the `let fmt;` block
  → rewritten to `dr._DASH_FMT_JS` plus the `let text;` block;
  `::test_the_displayed_value_is_identical_before_and_after_a_filter` (:457) reads
  `cfg["numfmt"]`-era fields → reads `cfg["fmt"]`.
- `test/test_help_claims_4.py::TestACardKeepsItsFormatWhenAFilterMoves` (:784-810; `_FORMATS`
  :780-782) — **kept and extended** with `%9,2fc`, `%10.0g`, `%td`, `%tdCCYY-NN-DD`, `%tm`
  on a date variable, and asserted against the fixture, not only against itself.
- `test/test_kpi_brush.py:251` slices `_FILTER_JS` up to the first `dash_apply_kpis(new_data,`
  (section 17's comment line after batch 2): unchanged by this section, and
  `TestConfig::test_the_brush_slice_markers_keep_their_order` guards the order.
- `test/test_filter_widget_data.py::TestADashboardOfKpisAlone::test_the_filter_recomputes_the_card_in_both_modes`
  is `function_test_map.py`'s test for `_parse_fmt` (:84) → the map entry is removed with
  the function.
- `test/test_display_format_writer.py::TestTheGuard::test_a_card_on_a_g_variable_is_unchanged_until_section_11`
  (section 04) → inverted: `%8.0gc` is now the effective format.
- `test/test_help_claims_4.cscript` HC4-12 (`fmt(%12s)` refused) stays.

## User stories

- **US-11.1** As a Stata user, I want `dash kpi mean(price), fmt(%10.0g)` to show
  `6165.257` — the text `display %10.0g` gives — on the page, after every filter move and
  after a brush, saved and served, so that the card reads as my Stata output does.
- **US-11.2** As a Stata user, I want a card with no `fmt()` to use the variable's own
  display format (`%8.0gc` for auto's price: `6,165.257`), and a date statistic of a date
  variable to use its `%t` picture (`%tdCCYY-NN-DD` gives `2000-01-02`), so that the card
  matches `list` and `summarize`.
- **US-11.3** As a dashboard viewer, I want a card whose filtered statistic is missing to
  read `.`, as Stata shows a missing value, in every mode and after every move.
- **US-11.4** As the maintainer, I want the JavaScript card rebuild to escape its text, so
  that a date picture carrying `!<` cannot inject markup after a filter move.
- **US-11.5** As the maintainer, I want a certification script that holds the rendered
  card to Stata's own display string for every accepted format, in both modes, so the
  promise is proven by Stata rather than by a number copied into a test.

## Business requirements

- **BR-11.1** For every format `dash kpi fmt()` accepts, the card's text at first paint,
  after a filter move and after a brush equals Stata's `display` text for that format
  applied to the statistic, trimmed, in the saved page and the served app.
- **BR-11.2** With no `fmt()`, the card uses the variable's display format when that
  format is writable and the statistic is in the variable's unit (a date-valued statistic
  of a date variable uses its `%t` picture; a count, distinct count, spread or skewness
  of a date variable uses `%9.0g`); otherwise `%9.0g`.
- **BR-11.3** A missing statistic reads `.` everywhere a card is written.
- **BR-11.4** A card's text is HTML-escaped by every writer that builds card markup.
- **BR-11.5** A card written with a format the page cannot write (a hand-edited spec
  carrying `%21x`) shows `%9.0g` with one note at build time; `dash kpi` itself refuses
  it (section 04).
- **BR-11.6** The card does not change text between first paint and the first move when
  no row is removed (the existing invariant), for every accepted format.
- **BR-11.7** Every changed card text is listed in CHANGELOG "Results that change" with
  the command, the old text and the new text.

## Technical requirements

- **TR-11.1 Effective format.** `_dash_effective_kpi_fmt(kpi, varname, formats=None,
  stat="", date_vars=None)`: explicit `fmt()` → else, for a date variable
  (`date_vars.get(varname)`), its own format when `_dash_kpi_date_valued(stat)` else
  `%9.0g` → else the variable's own format when `_dash_fmt_kind(own) in ("f", "g",
  "e")` → else `%9.0g`. Section 04's guard is removed. `formats` is the full map
  (saved `self.formats`; served `_FORMATS`). Callers: `DashRenderer._effective_kpi_fmt`,
  `_kpi_callback_config`, served `_format_kpi`.
- **TR-11.2 First paint.** `_dash_format_kpi_value(value, fmt_str, varname="", stat="",
  date_vars=None, storage=None)`: NaN/None → `.`; a date-valued statistic of a date
  variable → `_dash_fmt_text(_dash_stata_value_of(value, kind), fmt_str)`; otherwise
  `_dash_fmt_text(value, fmt_str, storage)`. The `date_formatter` parameter is retired.
  `_build_kpi_html`/`_format_kpi_value` pass `self.formats`, `self.date_vars`,
  `self.storage_types.get(varname)`; served `_format_kpi(value, fmt_str, varname, stat,
  date_vars)` passes `_FORMATS` and `_storage_types.get(varname)` (section 04 binds
  `_storage_types = meta.get('storage_types', {})` in `make_document`; read it, never
  rebind it).
- **TR-11.3 Config.** `_kpi_callback_config` emits `"fmt": kfmt` (the effective format,
  raw text; it is JSON-encoded into `kpi_config_json` and used only as `dash_fmt_text`'s
  argument), `"storage": self.storage_types.get(kvar, "")`, keeps `datekind` (set only for
  a date-valued statistic of a date variable), `use` (section 17's per-target list, never
  dropped), `name`, `name_html`, `stat`, `varname`, `has_qual`, `qual_ids`, `title`,
  `subtitle`, `text_color`, `color`, `bgcolor`; drops `decimals`, `commas`, `general`,
  `numfmt`. `_parse_fmt` and `_kpi_js_number_format` are deleted and removed from
  `function_test_map.py`.
- **TR-11.4 JavaScript.** In the body of `function dash_apply_kpis(` replace the date and
  number branches with: `let text; if (result === null || result === undefined ||
  Number.isNaN(result)) text = '.'; else if (k.datekind) { const sv =
  dash_stata_value_of(result, k.datekind); text = sv === null ? '.' : dash_fmt_text(sv,
  k.fmt); } else text = dash_fmt_text(result, k.fmt, k.storage);` and in the rebuild write
  `dash_html_escape(text)`. Nothing outside that body changes: section 17's per-group loop
  (calls `dash_apply_kpis(_grp_data, _grp.config, _grp.divs, ROW_ID)`) and its comment
  line `// dash_apply_kpis(new_data, ...) runs once per exclusion group below` stay
  exactly as they are, because the brush wiring (:23483-23485) and
  `test/test_kpi_brush.py:251` slice up to the FIRST `dash_apply_kpis(new_data,`, which is
  that comment. Delete `dash_tie_even` … `dash_numfmt` (about :14378-14482 at 91d97be;
  locate by the `function dash_tie_even(` and `function dash_numfmt(` lines) after
  `grep -n "dash_numfmt\|dash_fixed\|dash_expo\|dash_py_g\|dash_pystr\|dash_py_group\|dash_tie_even\|dash_py_exp"
  dash_render.py test/*.py` shows no other caller; keep the `// ---- KPI recompute, shared
  by` marker. The script text must satisfy `index("// ---- KPI recompute, shared by") <
  index("function dash_apply_kpis(") < index("dash_apply_kpis(new_data,")`, which
  `TestConfig::test_the_brush_slice_markers_keep_their_order` pins. `_DASH_FMT_JS` is
  already in scope (section 04 prepends it to `_DASH_FILTER_MASK_JS` and to the brush
  code).
- **TR-11.5 Served app.** `_format_kpi` (:25789-25803) becomes
  `_dash_format_kpi_value(value, _dash_effective_kpi_fmt({'fmt': fmt_str}, varname,
  _FORMATS, stat, date_vars), varname, stat, date_vars=date_vars,
  storage=_storage_types.get(varname))`; `_on_filter_change` (:26956) and the brush
  handler (:27040) are unchanged callers. The served card builder `_dash_kpi_card`
  escapes already (it wraps `_dash_kpi_card_html`).
- **TR-11.6 Missing.** `_dash_fmt_text` returns `.` for NaN/None in Python; the JS branch
  above returns `'.'`; `_dash_stata_value_of` returning None (a date past Stata's range)
  is `.` too.
- **TR-11.7 Refused format on a card.** A hand-edited spec whose `fmt` is `%21x` or
  unparseable: `_dash_effective_kpi_fmt` returns it as written; `_dash_fmt_text` writes
  `%9.0g` (section 04); `_build_kpi_html` and the served `make_document` warn once through
  `_dash_warn_once(("kpi-format", name), f"dash: KPI '{name}': fmt({fmt}) cannot be
  written by the dashboard; shown in %9.0g.")` when `_dash_fmt_refusal(fmt)` is not None.
- **TR-11.8 Both renderers.** No new module-level function is added here; the changed
  ones (`_dash_effective_kpi_fmt`, `_dash_format_kpi_value`) are already in the function
  copy list. `test/function_test_map.py` drops `DashRenderer._parse_fmt` and
  `DashRenderer._kpi_js_number_format` and names this section's tests for the two changed
  functions; `test/program_coverage_map.py` gains `test_gaps2_truth.cscript:KF-01` for
  `_dash_validate_value` and the `dash kpi` program (rule R2).
- **TR-11.9 Tests slicing `_FILTER_JS`.** `test_kpi_values.py::_js_format` and
  `test_date_range.py:995-1012` are rewritten to prepend `dr._DASH_FMT_JS` and slice from
  `"        let text;"` to `"        // Rebuild the complete Div HTML"`.
- **TR-11.10 Security.** The card text is escaped by `dash_html_escape` in the JS rebuild
  and by `html.escape` in Python; `k.fmt` never reaches `code`, HTML or CSS; `k.color`
  and `k.bgcolor` stay sanitised as today (`_resolve_kpi_color`).
- **TR-11.11 Certification.** KF-01..KF-05 are a block `* ==== S11 E1: KPI card text ====`
  of `test/test_gaps2_truth.cscript` (D11; the script S02 created and registered as runner
  block 67 with the hygiene pins set once), appended above its closing line
  `* ==== append new blocks above this line ====` in section order (rule R1 governs the
  block order); the block is guarded by `local only : env GAPS2_ONLY` so it runs alone
  under `GAPS2_ONLY=S11`. Case ids keep the `KF-` prefix so `program_coverage_map.py` and
  BUGS.md cite `test/test_gaps2_truth.cscript KF-01`.

## Boundaries

- Do not touch the widgets, tooltips, axes, facet titles, marker labels, CSV or colorvar
  labels (section 12), nor `_dash_stata_date_text`/`_format_date_value_standalone`
  (section 12 retires them once their last caller moves; it merges after this section).
- Do not touch the filter masks, `_dash_option_value`, the exclusion rule, the per-group
  KPI loop or its marker comment (section 17, on the tree) or the `_FILTER_JS`
  histogram/kdensity blocks (section 05).
- Do not change the statistic arithmetic (`_compute_kpi_stat_on_df`, `dash_pctl`, the
  served `_compute_kpi`); a spread of a date variable is still computed in
  milliseconds — its unit is not in E1/E3/G6 and is recorded in Notes, not fixed.
- `%x`/`%H` are refused, not written (PRD §7); the card-side fallback exists only for a
  hand-edited spec.
- Silent when honoured (Q22): a card that now honours `%10.0g` prints nothing; the only
  note is TR-11.7's.
- The BUGS.md entry for E1 lands closed in task 11-07's commit; E3's and G6's land in
  section 12.
- No new `.cscript` file, no edit to `test/run_all_cscripts.do` or
  `test/test_cscript_hygiene.py` (D11, rule R1).

## Stata truth

None added: this section consumes section 04's `format_truth.json` `kpi` block (Stata's
`display` text for each statistic × variable × format, with the statistic's value) and
its `date_formats` rows. The certification block computes its own expected strings in
Stata at run time (`: display …`), the pattern of `test_help_claims_4.cscript`, inside
`test/test_gaps2_truth.cscript`. Every Stata run goes through the slot wrapper (D6,
index.md step 0; it implements CLAUDE.md rule 10's console invocation under one of three
slots and sets `STATATMP=<scratch-dir>/tmp/`). A cscript resolves `cert_helpers.do`,
`cert_svg.do` and `adodir ".."` from `test/`, as `test/run_all_cscripts.do` does with its
`cd`, so it is run through a two-line driver written into the scratch directory:

```
mkdir -p /tmp/dash-s11
printf 'cd "%s/test"\ndo "%s/test/%s"\n' /Users/billy/Desktop/Programs/StataPrograms/d/dash /Users/billy/Desktop/Programs/StataPrograms/d/dash test_gaps2_truth.cscript > /tmp/dash-s11/run_test_gaps2_truth.do
GAPS2_ONLY=S11 scripts/stata_slot.sh /tmp/dash-s11 /tmp/dash-s11/run_test_gaps2_truth.do
```

Read `/tmp/dash-s11/run_test_gaps2_truth.log`; never relaunch to check. `GAPS2_ONLY=S11`
makes the truth script run only this section's block (the other blocks test
`inlist("`only'", "", "S<NN>")`). The script sets `$dash_nobrowser 1` itself (after
`cscript` drops globals) and exits 222 when `c(python_exec)` is empty; a SKIP is not a
pass.

## TDD test stubs

All in **`test/test_kpi_format.py`** (new, task 11-01) unless noted; helpers imported from
`test/test_help_claims_4.py` (`_saved`, `_saved_filter_move`, `_saved_brush`,
`_served_app`, `_served_session`, `_served_cards`, `_served_filter_move`, `_served_brush`,
`_cards`) and the auto frame from `test/fixtures/data/auto.csv`, with `when = 14610 + i`
(`%td`, i = 1..74) and `whenm = (year-1960)*12 + month-1` of `when` (`%tm`) so the fixture's
`kpi` rows (built on `sysuse auto` with `when = mdy(1,1,2000)+_n`, `whenm = mofd(when)`)
apply. Each stub names its pre-fix failure; 11-01 records every failure text in
`<scratch>/11-01-failure.txt` (Q24).

- Test: `TestFirstPaint::test_every_kpi_row_of_the_fixture_saved` — parametrised over
  the `kpi` rows: a spec with that statistic, variable and `fmt` (or none), formats
  `{price: %8.0gc, mpg: %8.0g, weight: %8.0gc, rep78: %8.0g, when: %td, whenm: %tm}`;
  assert the statistic's value equals the row's `value` (rtol 1e-9; the inputs are the
  same), then the card equals the row's `display`. Pre-fix: `%10.0g` row gives `6e+03`.
- Test: `TestFirstPaint::test_every_kpi_row_of_the_fixture_served` — the same through
  `_served_app`/`_served_cards`.
- Test: `TestAfterAMove::test_every_kpi_row_after_a_filter_move_saved` — a `mpg` slider
  moved to its minimum (no row removed): the card equals the row's `display`. Under node.
  Pre-fix: `dash_numfmt` text.
- Test: `TestAfterAMove::test_every_kpi_row_after_a_filter_move_served`.
- Test: `TestAfterAMove::test_a_move_that_removes_rows_recomputes_and_formats` — the
  slider at 25: the card equals `_dash_fmt_text` of pandas' statistic over `mpg >= 25`
  under the format, in both modes (the writer, not the fixture, is the oracle here; the
  fixture pins the writer).
- Test: `TestAfterABrush::test_the_brushed_card_is_formatted_in_both_modes` — indices
  [0, 1, 2] on the graph's source, `update(brush)`, `%10.0g` and `%tdCCYY-NN-DD`.
- Test: `TestMissing::test_a_missing_statistic_is_a_dot_everywhere` — `mean(price) if
  price > 1e9` and a date `max(when) if when > 1e9`: `.` at first paint, after a move and
  after a brush, saved and served. Pre-fix: `""` and `—` on the date card.
- Test: `TestEffectiveFormat::test_the_rule` — parametrised:
  `({"fmt": "%9.2f"}, "price", …) → %9.2f`; `({}, "price", {"price": "%8.0gc"}) →
  %8.0gc`; `({}, "when", formats {"when": "%tdCCYY-NN-DD"}, stat "max", date_vars) →
  %tdCCYY-NN-DD`; `({}, "when", …, stat "count") → %9.0g`; `({}, "price", {"price":
  "%21x"}) → %21x` (written in %9.0g by the writer, TR-11.7); `({}, "x", {}) → %9.0g`.
  Pre-fix: the guard returns `%9.0g` for `%8.0gc`.
- Test: `TestEscaping::test_the_js_rebuild_escapes_the_card_text` — a spec with
  `fmt("%td!<!b!>DD")` on `max(when)`: after a move under node, the Div text contains
  `&lt;b&gt;` and not `<b>`; the Python card too. Pre-fix: raw `<b>` after the move.
- Test: `TestEscaping::test_the_format_never_reaches_code_or_style` — the callback's
  `code` does not contain the format text; `kpi_config_json` holds it JSON-encoded only.
- Test: `TestRefusedOnACard::test_a_hand_edited_x_format_falls_back_with_one_note` —
  spec `fmt: %21x`: the card is `%9.0g`'s text, exactly one warning naming the KPI and
  `%21x`, both modes.
- Test: `TestConfig::test_the_config_carries_fmt_and_storage_and_not_the_legacy_fields`
  — `kpi_config_json` entries have `fmt`, `storage`, `datekind`, `use` and none of
  `numfmt`, `decimals`, `commas`, `general`; `dash_render` has no `_parse_fmt`,
  `_kpi_js_number_format`, and `_FILTER_JS` has no `function dash_numfmt(`.
- Test: `TestConfig::test_the_brush_slice_markers_keep_their_order` — in
  `dash_render._FILTER_JS`, `index("// ---- KPI recompute, shared by") <
  index("function dash_apply_kpis(") < index("dash_apply_kpis(new_data,")`, and the
  text `dash_apply_kpis(new_data,` occurs exactly once (section 17's comment line); the
  brush slice assembled at :23478-23496 therefore holds the whole rewritten body. A
  guard: it passes before and after this section's edits.
- Test (extended, `test/test_help_claims_4.py`): `TestACardKeepsItsFormatWhenAFilterMoves`
  `_FORMATS` gains `%9,2fc`, `%10.0g`, `%12,0gc`, `%09.2f`, `%tdCCYY-NN-DD`, `%tm` (the
  date ones on `when`), and a second assertion that each opened card equals
  `_dash_fmt_text` of the statistic.
- Certification block `* ==== S11 E1: KPI card text ====` of **`test/test_gaps2_truth.cscript`**
  (task 11-06): KF-01 saved page: for each format in `%9.0g %10.0g %9.2f %9,2fc %12.0fc
  %8.0gc %9.2e %9.3gc %-9.2f %09.2f` on `mean(price)` and `%td %tdCCYY-NN-DD
  %tdMonth_DD,_CCYY` on `max(when)`, `%tm` on `min(whenm)`, the page's card text (read by
  a Mata helper between `id="kpi_val_NAME"` and `</div>`) equals `${dash_kpi_<name>__dsp}`;
  KF-02 no `fmt()`: the card equals `: display %<own> value` for `mean(price)`
  (`%8.0gc`), `max(when)` (`%td`) and `%9.0g` for `count(when)`; KF-03 served: `dash
  build, saving(app.py) server replace`, then a `python:` block that `exec`s the app into
  a namespace, calls `make_document(Document())`, reads the `Div` texts and compares to
  the same globals, then moves the `mpg` slider to its minimum by firing its `_callbacks`
  (the `_served_filter_move` pattern) and compares again; KF-04 `mean(price) if price >
  1e9` reads `.` in both; KF-05 `fmt(%td!<!b!>DD)` on `max(when)`: the page holds
  `&lt;b&gt;`.

**Mutation table**:

| break this | test that must die |
|---|---|
| in `dash_apply_kpis` write `text` unescaped | `TestEscaping::test_the_js_rebuild_escapes_the_card_text` |
| in `_dash_effective_kpi_fmt` use the own format for `count` of a date variable | `TestEffectiveFormat::test_the_rule` and KF-02 |
| keep the `date_formatter` branch before the missing check | `TestMissing` (date card `""`) |
| pass epoch ms to `dash_fmt_text` without `dash_stata_value_of` | `TestAfterAMove` date rows |
| leave `numfmt` in the config and `dash_numfmt` in the page | `TestConfig` |
| served `_format_kpi` still using `_NUM_FORMATS` | `TestFirstPaint::…_served` (`%8.0gc` row) |
| delete section 17's marker comment while rewriting the body | `TestConfig::test_the_brush_slice_markers_keep_their_order` and `test_kpi_brush.py:251` |

## Test plan

| what | how | fixture | both modes? |
|---|---|---|---|
| Card at first paint equals Stata's display for every kpi row | pytest | format_truth.json `kpi` | yes |
| Card after a filter move (no rows removed) equals the same | pytest + node (saved), pytest (served) | format_truth.json | yes |
| Card after a move that removes rows is recomputed and formatted | pytest + node | none (writer is the oracle) | yes |
| Card after a brush | pytest + node | format_truth.json | yes |
| Missing is `.` | pytest + node | none | yes |
| Effective-format rule | pytest | none | n/a |
| JS rebuild escapes text; format never in code | pytest + node | none | saved |
| Hand-edited `%21x` falls back with one note | pytest | none | yes |
| Config shape; legacy writer gone; slice markers in order | pytest | none | saved |
| Card equals Stata's `kpi_display` per format, both modes, served move | block KF-01..05 of `test_gaps2_truth.cscript` | none (Stata computes) | yes |
| Format-keeping invariant across all formats | pytest (extended) | none | saved |

Acceptance criteria:

- **AC-11.1** `python3 -m pytest test/test_kpi_format.py test/test_help_claims_4.py
  test/test_kpi_values.py test/test_date_range.py test/test_server_layer_defects.py -q`
  passes with no skips under both interpreters.
- **AC-11.2** The `S11 E1` block of `test/test_gaps2_truth.cscript` passes KF-01..05 under
  `GAPS2_ONLY=S11` and inside the whole script; the script is S02's, registered once, and
  this section edits neither `test/run_all_cscripts.do` nor the hygiene pins (D11, R1).
- **AC-11.3** `grep -c "dash_numfmt\|_kpi_js_number_format\|_parse_fmt" dash_render.py`
  prints 0; `function_test_map.py` and `program_coverage_map.py` are current.
- **AC-11.4** The full pytest suite is green; BUGS.md carries E1 closed (`- Resolution:
  Fixed <ddmonyyyy> (WP-28, E1). …`) naming
  `test/test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved` and
  `test/test_gaps2_truth.cscript KF-01`; the `<!-- WP-28 E1 -->` marker in the `**WP-28
  (GAPS2 audit, 25sep2026)**` group of `### Results that change` is replaced by the E1 line
  ending `(WP-28, E1)`; dash.sthlp :1242-1261 describes the rule.

## Tasks

Commit boundary: **one commit (E1)** holding 11-01 to 11-07, subject ending `(GAPS2 E1)`,
made by 11-07 on the worktree branch `wp28-s11` after the section's one full pytest run in
the worktree (CLAUDE.md rules 4 and 11); the merger lands it on `s3-bugs` with the same
message (index.md step 1). The body opens with `<scratch>/11-01-failure.txt` (Q24) and
carries S01 TR-01.9's `Regression:` / `Flipped:` / `BUGS.md:` lines. Every Stata run goes
through `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6); the cscript through the
two-line driver of "Stata truth". No AI references anywhere.

<task type="auto" id="11-01">
  <name>Write the failing card tests</name>
  <files>test/test_kpi_format.py, test/test_help_claims_4.py</files>
  <action><![CDATA[
    Create `test/test_kpi_format.py`: import the render helpers from `test_help_claims_4` (they are module-level functions; import the module as `hc4`), load `test/fixtures/data/auto.csv` with pandas, add `when` and `whenm` as "TDD test stubs" specify, load `test/fixtures/format_truth.json` (`pytest.fail` naming section 04 if absent; never skip) and write every test named in "TDD test stubs" with exactly those names, including `TestConfig::test_the_brush_slice_markers_keep_their_order`. Parametrise the fixture-driven tests over the `kpi` rows by `(stat, var, fmt)` ids. The node runner is `hc4._run_js` (or `js_runner.JsSession` from section 03, on the tree since batch 1, for the after-move cases); skip only when node is absent and assert in a module test that the node tests ran. In `test/test_help_claims_4.py` extend `_FORMATS` (:780-782) and give `TestACardKeepsItsFormatWhenAFilterMoves` a date variable case and the `_dash_fmt_text` equality assertion. Do not touch dash_render.py. Run both files against the tree as batch 2 left it (sections 04 and 17 merged). Do not commit: save the failure output (`6e+03` for the `%10.0g` first-paint row, `""` and `—` on the missing date card, the raw bold tag after a move, `numfmt` present) to `<scratch>/11-01-failure.txt`; it opens the E1 commit's body and its `6e+03` is the CHANGELOG's old value (Q24, S01 TR-01.9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_kpi_format.py -q 2>&1 | tail -5` reports 0 passed apart from the marker-order guard, and no collection error; the `%10.0g` first-paint case fails with `6e+03`, not with an exception; `<scratch>/11-01-failure.txt` exists.]]></verify>
  <done>Every regression test of this section existed and failed for its recorded reason against the post-batch-2 tree, with nothing committed.</done>
</task>

<task type="auto" id="11-02">
  <name>Write the card through the writer first</name>
  <files>dash_render.py, test/function_test_map.py</files>
  <action><![CDATA[
    Rewrite `_dash_effective_kpi_fmt` as TR-11.1 (remove section 04's guard and its comment) and `_dash_format_kpi_value` as TR-11.2 (retire `date_formatter`; the docstring names the fixture). Update the saved callers `DashRenderer._effective_kpi_fmt`, `_format_kpi_value` (:21354) and `_build_kpi_html` (:23374) to pass `self.formats`, `stat`, `self.date_vars` and `self.storage_types.get(varname)`, and add TR-11.7's one-time note in `_build_kpi_html`. Rewrite the served `_format_kpi` (:25789-25803) as TR-11.5 with the same note, reading `_storage_types`, which section 04 already binds in `make_document` as `_storage_types = meta.get('storage_types', {})`; do not rebind it. Update `test/function_test_map.py` entries for the two functions to this section's tests.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_kpi_format.py -q -k "TestFirstPaint or TestEffectiveFormat or TestRefusedOnACard or (TestMissing and not move and not brush)"` passes; `python3 -m pytest test/test_server_layer_defects.py -q -k TheKpiFormatHelpers` shows only the `date_formatter` test failing (flipped in 11-04).]]></verify>
  <done>Every card's first paint, saved and served, became Stata's text for its effective format, missing read `.`, and a hand-edited refused format fell back with one note.</done>
</task>

<task type="auto" id="11-03">
  <name>Write the card through the JS twin</name>
  <files>dash_render.py, test/function_test_map.py, test/test_kpi_values.py</files>
  <action><![CDATA[
    In `_kpi_callback_config` (:23385-23451 at 91d97be; section 17 already added `"use"` to each entry) emit `fmt` and `storage` and drop `decimals`, `commas`, `general`, `numfmt` (TR-11.3); delete `_parse_fmt` (:22996) and `_kpi_js_number_format` (:23004-23042) and their `function_test_map.py` entries. In `_FILTER_JS` rewrite ONLY the body of `function dash_apply_kpis(`: replace the date and number branches and escape the rebuild (TR-11.4), renaming the local `fmt` to `text`; leave section 17's per-group loop and its comment line `// dash_apply_kpis(new_data, ...) runs once per exclusion group below` exactly as they are (the brush wiring at :23483-23485 and `test/test_kpi_brush.py:251` slice up to the FIRST `dash_apply_kpis(new_data,`, which is that comment). After the grep TR-11.4 prescribes shows no other caller, delete the `dash_tie_even` … `dash_numfmt` block (about :14378-14482 at 91d97be; locate it by the `function dash_tie_even(` and `function dash_numfmt(` lines) and its banner comment, keeping the `// ---- KPI recompute, shared by` marker. Rewrite `test_kpi_values.py::_js_format` as TR-11.9 and make `test_the_displayed_value_is_identical_before_and_after_a_filter` read `cfg["fmt"]`. Confirm the brush wiring still slices cleanly by rendering a spec with `update(brush)` and running the attached code under node.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_kpi_format.py -q -k "TestAfterAMove or TestAfterABrush or TestEscaping or TestConfig or TestMissing"` passes; `python3 -m pytest test/test_kpi_values.py test/test_kpi_brush.py test/test_help_claims_4.py -q -k "Filtering or KeepsItsFormat or brush"` passes; `grep -c "function dash_numfmt(" dash_render.py` prints 0; `python3 -c "import dash_render as d;s=d._FILTER_JS;assert s.index('// ---- KPI recompute, shared by') < s.index('function dash_apply_kpis(') < s.index('dash_apply_kpis(new_data,');assert s.count('dash_apply_kpis(new_data,') == 1"` prints nothing.]]></verify>
  <done>After a filter move and after a brush the saved page wrote every card through `dash_fmt_text` and escaped its text, the legacy writer and its config fields were gone, and section 17's loop and marker comment were untouched.</done>
</task>

<task type="auto" id="11-04">
  <name>Flip the pinned card tests to Stata's text</name>
  <files>test/test_date_range.py, test/test_server_layer_defects.py, test/test_display_format_writer.py</files>
  <action><![CDATA[
    Flip, with a comment naming E1 and this section: `test_date_range.py::… test_a_kpi_reads_the_placeholder_as_its_date` (:545) to `31dec9999`/`02jan2001`; `test_the_page_callback_writes_a_kpi_year_in_four_digits` (:995-1012) to slice from `"        let text;"`, prepend `dr._DASH_FMT_JS`, set `k = {datekind: kind, fmt: "%"+kind}` and expect `01jan0100`, `0100`, `0100m1`, `01jan0100 00:00:00` (the fixture's `%ty` and `%tm` rows for year 100 decide the exact text; read them); `test_server_layer_defects.py::TestTheKpiFormatHelpers::test_a_date_valued_statistic_is_shown_as_a_date` to pass `date_vars={"date": "td"}` and `"%td"` and expect `02jan2002`, and add a `%tdCCYY-NN-DD` case; invert `test_display_format_writer.py::TestTheGuard::test_a_card_on_a_g_variable_is_unchanged_until_section_11` into `test_a_card_on_a_g_variable_uses_its_own_format` (`%8.0gc`). Record each old/new text as a `Flipped: <node> -- <old expectation> was wrong because <why>` line in `<scratch>/11-flips.txt` for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_date_range.py test/test_server_layer_defects.py test/test_display_format_writer.py -q` passes; `<scratch>/11-flips.txt` holds one `Flipped:` line per changed assertion.]]></verify>
  <done>Every test that pinned the old card text pinned Stata's, none was deleted, and each flip was recorded for the commit body.</done>
</task>

<task type="auto" id="11-05">
  <name>Flip the remaining card pins</name>
  <files>test/test_filter_widget_data.py, test/test_adversarial_matrix.py, test/test_mode_parity.py</files>
  <action><![CDATA[
    Run `python3 -m pytest test/test_filter_widget_data.py test/test_adversarial_matrix.py test/test_mode_parity.py test/test_function_test_map.py test/test_resource_limits.py -q` (changed files only; the section's one full run is 11-07's). Expected fallout, each flipped with a comment citing this section: any assertion on a card's text for a variable carrying a `%g` format (`test_filter_widget_data.py::TestADashboardOfKpisAlone`), any assertion that `_dash_format_kpi_value` returns Python's `:g` text (`test_adversarial_matrix.py::TestNumericFormatBounds::test_a_hand_edited_kpi_format_is_bounded` keeps its bound and its `1.50`/`1,234.5` cases, which Stata agrees with), and any parity profile that recorded a card's old text (`test_mode_parity.py` CORPUS entries with KPIs are re-profiled; this section edits neither `ALLOWED` nor `_MUST_WARN`, rule R6). Anything else is a regression of this section: fix the code, not the test. Add every flipped assertion with old and new text to `<scratch>/11-flips.txt`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_filter_widget_data.py test/test_adversarial_matrix.py test/test_mode_parity.py test/test_function_test_map.py test/test_resource_limits.py -q 2>&1 | tail -3` reports no failures and no new skips; `python3 -m pytest test/test_resource_limits.py -q -k DefinesEveryName` passes.]]></verify>
  <done>Every re-baselined card assertion in the three files was flipped with its reason recorded, and the served app defined every name it read.</done>
</task>

<task type="auto" id="11-06">
  <name>Certify the card against Stata's display</name>
  <files>test/test_gaps2_truth.cscript, test/program_coverage_map.py</files>
  <action><![CDATA[
    Append to `test/test_gaps2_truth.cscript` (S02 created it in batch 1 and registered it as runner block 67; it opens with the Python gate that exits 222, loads `cert_helpers.do` and `cert_svg.do`, sets `global dash_nobrowser 1`, and ends with the line `* ==== append new blocks above this line ====`), above that last line and after every earlier section's block (rule R1: blocks in section order), the block
```
* ==== S11 E1: KPI card text ====
local only : env GAPS2_ONLY
if inlist("`only'", "", "S11") {
    display as text "S11 start `c(current_time)'"
    ... KF-01..KF-05 ...
    display as text "S11 end `c(current_time)'"
}
* ==== end S11 ====
```
    holding inside the `if`: `sysuse auto, clear`, `generate when = mdy(1,1,2000) + _n`, `format when %td`, `generate whenm = mofd(when)`, `format whenm %tm`; a Mata helper `_kf_card(path, name)` returning the text between the value div's opening tag (the one whose id is `kpi_val_` followed by the KPI's name) and its closing div tag; and KF-01..KF-05 as "TDD test stubs" specify, each displaying `KF-0n PASS` or `KF-0n FAIL: <why>` through the script's PASS/FAIL helper and never `exit`ing on a failure, so the blocks after it still run. For KF-03 the `python:` block reads the expected strings from the `dash_kpi_*__dsp` globals through `sfi.Macro.getGlobal`, `exec`s the app file into a dict (the generated app, never user data), builds a `bokeh.document.Document`, fires the `mpg` slider's `_callbacks` as `test_help_claims_4.py::_served_filter_move` does, and raises on any mismatch (the block never calls back into Stata). Edit neither `test/run_all_cscripts.do` nor `test/test_cscript_hygiene.py` (D11: S02 alone set the pins). Add `test_gaps2_truth.cscript:KF-01` to `test/program_coverage_map.py` as an `e2e` reference for `_dash_validate_value` and the `dash kpi` program. Run the block with the driver of "Stata truth" under `GAPS2_ONLY=S11` and read `/tmp/dash-s11/run_test_gaps2_truth.log`.
  ]]></action>
  <verify><![CDATA[`grep -c "KF-0[1-5] PASS" /tmp/dash-s11/run_test_gaps2_truth.log` prints 5, `grep -c " FAIL" /tmp/dash-s11/run_test_gaps2_truth.log` prints 0 and `grep -c '^r([0-9]*);' /tmp/dash-s11/run_test_gaps2_truth.log` prints 0; `python3 -m pytest test/test_cscript_hygiene.py test/test_program_coverage_map.py -q` passes.]]></verify>
  <done>Stata itself certified, in a block of the one truth script, that the saved page and the served app show its `display` text for every accepted card format before and after a served filter move.</done>
</task>

<task type="auto" id="11-07">
  <name>Close E1 in BUGS.md, help and changelog</name>
  <files>BUGS.md, dash.sthlp, CHANGELOG.md</files>
  <action><![CDATA[
    Append at the end of BUGS.md (S01 TR-01.8; never mid-file) the closed entry `- [x] Title: KPI fmt() accepts formats the card then does not apply, and %w.0g rounds the card to one significant digit` with the fields in order (File Names and Line Numbers: dash_render.py `_dash_format_kpi_value`, `_kpi_callback_config`, `dash_apply_kpis`, the served `_format_kpi`; Description: GAPS2 E1's measured symptoms and the known residual that a spread of a date variable is computed in milliseconds; Suggested fix: one writer of Stata formats) and `- Resolution: Fixed <ddmonyyyy> (WP-28, E1). Every card, at first paint, after a filter move and after a brush, is written by _dash_fmt_text / dash_fmt_text under its effective format (fmt(), else the variable's own display format, else %9.0g) in _dash_format_kpi_value, _kpi_callback_config, dash_apply_kpis and the served _format_kpi, in both renderers; a missing statistic reads .; the JavaScript rebuild escapes its text; %x and %H are refused by section 04's change. Pinned by test/test_kpi_format.py::TestFirstPaint::test_every_kpi_row_of_the_fixture_saved, ::TestAfterAMove::test_every_kpi_row_after_a_filter_move_saved, ::TestEscaping::test_the_js_rebuild_escapes_the_card_text, test/test_gaps2_truth.cscript KF-01.` -- the title holds no `"`. Rewrite dash.sthlp :1242-1250 (a date statistic is shown in the variable's own picture, or `fmt()`'s) and :1259-1261 (the effective-format rule of BR-11.2, the accepted families, `.` for missing); grep `test/test_help_claims_4.py` and `test/test_help_claims_4.cscript` for the changed sentences and update any pin. In `CHANGELOG.md` replace the marker `<!-- WP-28 E1 -->` in the `**WP-28 (GAPS2 audit, 25sep2026)**` group at the end of the release's `### Results that change` list (S01 placed it there, D2) with ONE line ending `(WP-28, E1)` that names the command, the old value and the new: `dash kpi mean(price), fmt(%10.0g)` read `6e+03` (the value `<scratch>/11-01-failure.txt` recorded, Q24), now `6165.257`; without `fmt()` on auto's price `6165.26`, now `6,165.257` (its `%8.0gc`); `max(when)` on a `%td` variable `02 Jan 2001`, now `02jan2001`; a missing date card `—`, now `.`; and the sentence that the page's card rebuild now escapes its text (no separate security line). Write nothing under any other heading. Run the section's one full pytest run in the worktree (`python3 -m pytest test/ -q`; a pin it exposes that 11-05 did not list is flipped in 11-05's files before continuing), then the S11 block through the driver; grep the three files and the message for `claude|anthropic`; commit the whole section on the worktree branch `wp28-s11` as ONE commit, subject ending `(GAPS2 E1)`, body opening with `<scratch>/11-01-failure.txt` and carrying the `Regression:` / `Flipped:` (from `<scratch>/11-flips.txt`) / `BUGS.md: "<title>" (closed)` lines (S01 TR-01.9); the merger lands it on `s3-bugs` with this message (index.md step 1).
  ]]></action>
  <verify><![CDATA[The full suite's tail reports no failures and no new skips; `python3 -m pytest test/test_tracking_documents.py test/test_help_claims_4.py -q` passes (the new entry parses, names existing tests, and no open S1/S2 entry exists); `grep -c '<!-- WP-28 E1 -->' CHANGELOG.md` prints 0 and `grep -c '(WP-28, E1)' CHANGELOG.md BUGS.md` prints 2; `git log -1 --format=%B | grep -ci "claude\|anthropic"` prints 0 and `git log -1 --format=%s | grep -c '(GAPS2 E1)'` prints 1.]]></verify>
  <done>E1 was closed in BUGS.md naming its tests, the help stated the card's format rule, the E1 CHANGELOG marker was replaced by the line with the recorded old values, and one green commit on `wp28-s11` carried the section.</done>
</task>

## Section completion criteria

- Every card, saved and served, at first paint, after a filter move and after a brush,
  equals Stata's `display` text for its effective format on every `kpi` fixture row, and
  `.` when missing; the `S11 E1` block of `test/test_gaps2_truth.cscript` proves it from
  Stata in both modes.
- `dash_numfmt` and its family, `_parse_fmt` and `_kpi_js_number_format` are gone; the
  config carries `fmt`, `storage` and section 17's `use`; the JS rebuild escapes its
  text; section 17's per-group loop and its marker comment are untouched and
  `TestConfig::test_the_brush_slice_markers_keep_their_order` passes.
- One commit on `wp28-s11`, subject ending `(GAPS2 E1)`, holding the failing tests, the
  fix, the flips and the closed BUGS.md entry; no test-only commit exists (D1).
- The full pytest suite is green with no skips; every flipped assertion is recorded as a
  `Flipped:` line; no new `.cscript` file, no runner or hygiene-pin edit (D11).
- BUGS.md carries E1 closed with `- Resolution: Fixed <ddmonyyyy> (WP-28, E1). …`;
  dash.sthlp :1242-1261 is updated; the `<!-- WP-28 E1 -->` marker is replaced by a line
  ending `(WP-28, E1)`.

## Notes

- **Two truths for a card without `fmt()`.** Stata's `kpi_display` is the raw macro text
  in that case; dash's documented rule is the variable's own format. The fixture's `kpi`
  rows and KF-02 use `: display %<own> value`; never compare a no-`fmt()` card to
  `__dsp`.
- **A count of a date variable is a count.** The own-format rule applies only to a
  date-valued statistic (`_dash_kpi_date_valued`); `count(when)`, `dcount`, `sd`, `var`,
  `cv`, `skewness`, `iqr` and `sum` of a date variable use `%9.0g` unless `fmt()` says
  otherwise. The spread of a date variable is still computed in milliseconds in both
  modes (Stata's `summarize` gives days); that is outside E1/E3/G6 and is recorded in
  the E1 entry's Description as a known residual, not fixed here.
- **Epoch milliseconds.** A date statistic reaches both writers as milliseconds; convert
  with `_dash_stata_value_of`/`dash_stata_value_of` before formatting. A value past
  31dec9999 converts to None and prints `.`.
- **Slice markers.** The brush wiring, `test_kpi_brush.py:251` and two tests slice
  `_FILTER_JS` by text; keep `// ---- KPI recompute, shared by` where it is, leave section
  17's comment line `// dash_apply_kpis(new_data, ...) runs once per exclusion group
  below` (the first and only `dash_apply_kpis(new_data,`) and its loop untouched, and
  update the tests' `let fmt;` marker to `let text;`.
- **Commit bodies** use S01 TR-01.9's line forms verbatim: `Regression:
  test/<file>.py::<Class>::<test> -- failed at <pre-fix tree> with <text>`, `Flipped: <node>
  -- <old expectation> was wrong because <why>` (one per flip), `BUGS.md: "<title>"
  (closed)`; no `Fixture:` line (this section regenerates none).
- **Shared registries (rules R1-R6).** R1: the KF cases are a block of
  `test_gaps2_truth.cscript` appended above its closing line, in section order; the runner
  and the two hygiene pins are never edited here. R2: `function_test_map.py` loses the two
  deleted names and `program_coverage_map.py` gains the KF-01 reference, each in
  alphabetical place; no copy-list entry changes. R3: BUGS.md is appended at the end, only
  the E1 marker is replaced in CHANGELOG, and dash.sthlp :1242-1261 is the one help region
  this section owns. R6: `CORPUS` entries with KPIs are re-profiled only; `ALLOWED` and
  `_MUST_WARN` are never edited here.
- **Renderer order.** The served `_format_kpi` is a module-level function in the app and
  resolves `_FORMATS`/`_storage_types` from module scope; the saved renderer reads
  `self.*`. Both call the same two module functions, so parity is by construction; the
  tests still assert both.
- **Section 12 (merged after this section in batch 3) will retire
  `_format_date_value_standalone`.** After this section its only callers are section 12's
  sites; do not delete it here.
- **Stata invocation.** Every run is `scripts/stata_slot.sh <scratch-dir> <file>.do` (D6):
  the wrapper takes one of three `mkdir` slots, sets `STATATMP=<scratch-dir>/tmp/`
  (trailing slash) and runs Stata's console binary in batch; never the GUI, never a bare
  `stata-mp`, never the full cert suite inside a section (S19 runs it). A cscript needs
  the two-line driver of "Stata truth" because it resolves its helpers from `test/`.
- **python_exec hazard.** Many concurrent Stata sessions can drop `python_exec` from
  `~/.stata19/console/stata19.rc`; the truth script then exits 222 and a SKIP is not a
  pass: check `c(python_exec)` before trusting a skip.
- **Line numbers** are 91d97be's, shifted by sections 04 and 17 (batch 2); symbols are
  authoritative.
