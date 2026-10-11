# Section 42: Time-series operators in plot varlists (P1.7)

> Part of: WP-30 · Items: P1.7 (entry `P1.7`; GAPS2-G4-a, G4-b, G4-c) · Risk: yellow · Batch: 15 (merge order S42, S43, S44) · Depends on: 02, 19 · Blocks: none · Tasks: 18, 2 commits (operators drawn, then twoway's refusals and display names) · Case prefix: TSO

## Review amendments

- Fixed (major): `$S` was this review session's scratchpad and shared by S42, S43 and S44, which run in parallel and write the same log names (`run_test_parser.log`, `run_test_wp30_truth.log`) and slot directory. `$S` is now `<scratch>/s42`; the batch base, impact file and queue script are read from `<scratch>`.
- Fixed (major): TR-42.5 subtracted "the ts expressions" from `needed_vars`, but after the rewrite `_dash_extract_vars` (:6531) collects the `__dasht<k>` names, which do not exist until `_dash_tsop_gen`; `_dash_formats_json` would have failed on them. The names are now removed after :6583.
- Fixed (major, M5): the canonical rule held the base to ASCII, refusing a Unicode-named variable that twoway accepts and `_dash_is_stata_name` admits. Mata now checks the operator bytes and an exact existing variable name (byte loop, no `regexm`); the renderer checks the base with `_dash_is_stata_name`; both admit the same digit range. Test rows added.
- Fixed (major): 42-03's verify required TSO-04 (types drawn), which needs 42-06's export; it now checks TSO-05 only and 42-06 checks TSO-04.
- Fixed (minor): TR-42.7 said `_dash_qual_gen` is `sortpreserve` (it is not, :4773); the note map for `_dash_load_columns` is read from the spec, since both load calls run before the take-outs (:29321/:29335, :34624/:34632); 42-11 stops and reports a found pin instead of editing a file outside its `<files>`; the truth block states TR-01.10's form (exact header, `w30_work`, run alone).
- Checked: anchors `_dash_parse_varpart_std` :1310/:1322, the five dispatch calls, `_dash_take_qual_columns` :27657 and its gate, `_DASH_QUAL_NAME_RE` :27608, `_dash_csv_meta` :17298 and callers :32384/:36200, `_DASH_CSV_JS` header :18401, copy-list anchors :32979/:33153; `_dash_take_sort_columns` does not refuse reserved columns, so `keep` on the qualifier gate suffices; `ServerAppBuilder._frame` inherits `_load_data`. No function is shared with S43 or S44 (S42 is batch 15's only `_generate_app_source` editor).
- Rejected: 42-12's `<files>none</files>`. It is the commit step of commit 1 and stages what 42-03..42-11 wrote; folding it into a documentation task would mix the help edit with the full run.
- The review pass applied both lenses.

**Binding readings applied in this file** (M1, M2, M5, M6; register P1.7.1-P1.7.5, X.1, X.5; index A141, A148, A149, A156, R1-R12):
- **M5 / P1.7.1.** What twoway refuses is refused in its words and codes: no `tsset` r(111) `time variable not set`; a string base r(109) `<var>:  may not use time-series operators on string variables`; a factor variable r(101) `factor-variable operators not allowed`; an unknown operator r(198) `<op>:  operator invalid`; operators on fpfit, fpfitci, lowess, lpoly, lpolyci, histogram and kdensity keep r(101) `factor-variable and time-series operators not allowed`; `by()` with an operated plot variable r(5) `not sorted`, then one dash hint line; a bare `sort` with an operated x on the 18 types twoway refuses it on r(198), twoway's two lines.
- **M6.** Nothing is printed where twoway prints nothing: an operated series with gaps draws silently.
- **M1 / P1.7.5.** Titles and keys are twoway's text: the base's label, `, `, the normalised operator (`Closing price, D`), or the expression when the base has no label (`D.y2`). `D.`/`S.` of a `%t` base carry the base's format, as twoway does.
- **P1.7.2.** The CSV header of an operator column is the expression as typed after twoway's normalisation (`L.close`), and so is any note that names it. `__dasht<k>` never reaches the user.
- **P1.7.3.** `[aw=L.x]` stays refused (GAPS2-G17 is P2.14). The shared "evaluated column" helper is P2.14's; this section's generator is written so P2.14 can call it.
- **P1.7.4 / M2.** Truth is StataNow 19.5 only.
- **Reading of the manifest's "titles and keys read 'D.close'".** PLAN BR-30.7's "the expression as typed" is twoway's text for an unlabelled base; a labelled base reads `<label>, D`, measured (Evidence E6). M1 decides: twoway's text. The register's P1.7.2 expression form binds the CSV header and notes only.
- **A156.** Two commits. Commit 1 leaves the BUGS.md entry, its `WP30_OPEN` key and both markers; commit 2 closes all three.

## Overview

**What is wrong today.** DROPIN-REMAINING.md:97 (P1.7): "Time-series operators in plot varlists are refused r(101). This covers `line D.close date`, `tsline D.gdp` and `lfit y L.x`, and the help does not document it." GAPS2.md G4 (:1378, :1417-1422) filed it unmeasured. Re-measured at `c96facd` (research `.ultraplan/wp30/research/p1-07.md` §1-2, critic c1-c3, StataNow 19.5):

```
dash line D.close date, name(g1)     -> r(101) "factor-variable and time-series operators not allowed"   (twoway rc 0)
dash tsline D.close                  -> r(101)                                                          (twoway rc 0)
dash lfit close L.close              -> r(101)                                                          (twoway rc 0)
dash scatter D.close LD.close        -> r(101)                                                          (twoway rc 0)
no tsset: dash line L.close t        -> r(101)            (twoway: "time variable not set", r(111))
dash scatter L.make mpg              -> r(101)            (twoway: "make:  may not use time-series operators on string variables", r(109))
dash scatter i.foreign mpg           -> r(101), dash's words (twoway: "factor-variable operators not allowed", r(101))
```

**After this section,** in the saved page and the served app, before and after every filter move:
- `L.`, `F.`, `D.`, `S.`, their combinations and `L(1/2).x` are accepted in plot varlists on every type twoway accepts them on: scatter, line, connected, area, bar, spike, dropline, dot, lfit, qfit, lfitci, qfitci, mspline, mband, the eight range types, the five pc types, tsline and tsrline;
- each distinct expression is computed once by Stata at build, under the `tsset` then in force, over all observations, into a `__dasht<k>` column of `tsrevar`'s storage type with the base's format and value label; `if`, `in` and filter moves select rows of the computed series, as twoway's `if` does;
- titles, keys and tooltips read twoway's text; the CSV header and notes read the expression;
- twoway's refusals are dash's (M5), on the one-line route, `dash build` and `dash serve`.

**Why one section, two commits.** P1.7 is one item (A138). Commit 1 is "operators drawn": the parsers, the Mata rewrite, `_dash_tsop_gen`, both export blocks, the renderer's take-in and labels in both modes, filter moves and help. Commit 2 is "twoway's parity edges": the `by()` and bare-`sort` refusals, the CSV header, note display names and the reserved-prefix wording. Commit 2 needs commit 1's columns; neither is red.

**Test order and commit rule (rule 7, A156).** Two cycles on `wp30-s42`.
- **Commit 1:** 42-01 and 42-02 write the fixture and every commit-1 regression test, run them on the unmodified batch-15 base and save `$S/42-P1.7-1-failure.txt` (no commit); 42-03 to 42-11 fix and document; 42-12 runs the full suite and makes commit 1, leaving the entry, its key and both markers.
- **Commit 2:** 42-13 writes the commit-2 tests against the tree commit 1 left and saves `$S/42-P1.7-2-failure.txt`; 42-14 to 42-17 fix; 42-18 closes the entry, deletes the key, replaces both markers and makes commit 2.

## Risk: [yellow] — the reserved-column gate, both export blocks and one CRITICAL renderer symbol

**Why.**
- `_dash_csv_meta` is CRITICAL (research §6: 8 processes through `_csv_button`, `_build_filter_widgets`, `render`; plus the served codegen at :36200): warn before editing.
- `ServerAppBuilder._generate_app_source` and `_glyph_layer_lines` are HIGH. S42 is batch 15's one template editor (R12).
- `_dash_take_qual_columns` (LOW, 1 direct, plus the served codegen at :34633) is the reserved-column security gate (G1, WP-28).
- Every Stata and Mata symbol is UNKNOWN to the index (callers by grep, research §6 and critic): `_dash_parse_varpart_std` (one call, :3797), `_3v` (:3601), `_4v` (:3652), `_dash_process_segment` (`_dash_plot` :5210), `_dash_plot`, `_dash_render_immediate`, `_dash_prepare_spec` (:8192 build, :8352 serve), `_dash_qual_gen` (:6725, :7873; message only).

**Risk factors.**
1. The empty-variable checks fire before any ts column exists, so a graph whose every plot variable is an operator would be refused r(198) (critic gap 1: dash.ado:6606-6612, :7770-7780).
2. `_dash_prepare_spec` reads plot variables from the raw registry (`_dash_extract_vars` on `${dash_json_<g>}`, :7619), so `L.close` would reach `_dash_write_data`'s `unab` (:4544) and fail (critic gap 2).
3. The `_estimates hold` guards (:6721, :7869) count only `_dq_n + _ds_n` (critic gap 3).
4. `ServerAppBuilder._frame` (:33819) calls `DashRenderer._load_data` on a `__new__` instance for build-time checks, a second caller of the take-in (critic gap 4).
5. The registry is ordinary globals a do-file can edit; an expression reaching `tsrevar` unchecked is code-adjacent.
6. The served copy loop skips a misspelt name silently (RK-9).

**Mitigation.**
1. Both checks count `_dts_n` (TR-42.6, TR-42.7); TSO-13 draws `scatter D.close LD.close` on every route.
2. `gvars` is read from the ts-rewritten graph (TR-42.7).
3. Both guards count `_dts_n` (TR-42.6, TR-42.7).
4. A served build-time refusal of a bad `ts_cols` is tested (`TestTakingTheColumnsIn::test_served_build_refuses_a_bad_map`).
5. Every expression is re-checked against the canonical form and its base against `_st_varindex` before `tsrevar` sees it (TR-42.4); TSO-11 hand-edits the registry.
6. G4 guards run in 42-08 and 42-09 where the names land.

## Dependencies

- **Depends on: 02, 19.**
  - S02 (batch 1): the path-free extractor stanza (TR-02.9) the new extractor copies, `scripts/stata_slot.sh`, and the `stata_base()`/`stata_plus()` constants of `test/test_help_claims_1.py` (:76-78) that 42-11 edits beside.
  - S19 (batch 7): `_dash_layer_series(plot, var_labels=None, default_level=None)` and `_dash_axis_default_titles`, which read every key and title through `_dash_var_label(var_labels, name)`. S42 gives them twoway's text by putting it in the variable labels (TR-42.9); it edits neither helper.
  - S01 provides the open entry `P1.7` ("Time-series operators in plot varlists, such as line D.close date and lfit y L.x, are refused r(101)"), its `WP30_OPEN` key, the markers `<!-- WP-30 P1.7 -->` at the end of `### New` and of `### Changed behaviour (may need your do-files changed)`, the S42 stub block of `test/test_wp30_truth.cscript` and the map anchors `# WP-30 S42 (P1.7): Time-series operators in plot varlists (P1.7)`.
  - Landed before and read here: S03 (`version 19` on every new program), S06 (notes through `_dash_warn_once`), S12, S22 and S34 (their export-block paragraphs, R6), S18 (default tick text from a column's format), S29 (titles and keys translated once at the sink), S35 (a `%t` column draws on a date axis).
- **Blocks:** none (manifest). P2.14 reuses `_dash_tsop_gen`'s lifecycle for `[aw=L.x]`.
- **Parallel batch: 15**, merge order S42, S43, S44. S42 lands first.
- **Can run with:** S43 edits the four appliers, the colour mappers and the colour readers; S44 edits S21's finishers, `_dash_apply_axis_options`, `_dash_finish_secondary_axes` and the date ticker. S42 edits none of them, and neither partner edits dash.ado, dash_parse.mata, `_load_data`, `_dash_take_qual_columns`, `_dash_csv_meta` or `_generate_app_source`.

## Evidence

Anchors are at `c96facd` (dash.ado 8,487 lines, dash_parse.mata 6,093, dash_render.py 37,689, dash.sthlp 3,822), re-verified for this file. S02-S41 land before batch 15 and move many of them; the executor re-finds each by symbol at `batch-15-base` and treats the numbers as approximate.

### E1. The parsers declare `varlist(numeric)` with no `ts` (dash.ado)

`_dash_parse_varpart_std` (:1310), `_1v` (:1345, `varname(numeric)`), `_3v` (:1382), `_4v` (:1415). The std form:

```stata
1310 program define _dash_parse_varpart_std, sclass
1311     version 16.0
...
1322     syntax varlist(numeric) [if] [in] [aweight fweight pweight iweight]
```

Their calls: `_1v` :3595, `_3v` :3601, `_4v` :3652, `_any` :3674, `_std` :3797 (`_dash_parse_varpart_std `macval(varpart)'`, then `local vl = "`s(varlist)'"`).

### E2. twoway's rules (research §2, measured; sp500, `tsset t` unless named)

```
rc 0   : scatter line connected area bar spike dropline dot lfit qfit lfitci qfitci mspline mband
         rarea rbar rspike rcap rline rconnected rcapsym rscatter
         pcspike pcarrow pcbarrow pcscatter pccapsym  tsline (D.close)  tsrline (L.low L.high)
rc 101 : fpfit fpfitci lowess lpoly lpolyci histogram kdensity
         "factor-variable and time-series operators not allowed"
tsunab z : l.close DL.close d.l.close L1.close L0.close S1.close L(0/2).close
  -> L.close LD.close LD.close L.close close S.close close L.close L2.close
tsyn L(1/2).close t -> L.close L2.close t        tsyn L.(mpg weight) t -> L.mpg L.weight t
tsyn L.mp t -> L.mpg t (abbreviation)            no tsset -> "time variable not set" r(111)
L.make -> "make:  may not use time-series operators on string variables" r(109)
i.foreign -> "factor-variable operators not allowed" r(101)
L.nosuch -> "variable nosuch not found" r(111)   X.mpg -> "X:  operator invalid" r(198)
```

`syntax varlist(numeric ts)` gives every one of these words itself, and hands back the normalised list.

### E3. Values, types, formats, value labels (research §2.4)

- Computed over the full data: `twoway scatter D.close t if t>5 & t<9` holds D.close = 4.940063 at t = 6, `close[6]-close[5]`; the lag reaches the excluded row.
- Panels: under `xtset id tt` (2 × 10), `scatter L.y tt` has one missing L.y at each panel's start. Gaps: under `tsset date`, D.close is non-missing on 192 of 248 rows.
- Storage follows `tsrevar`: `D.x` (double) double, `D.xf` (float) float (serset equal to `gen double = D.x` with sum |diff| 0; `gen double = D.xf` off by 0.000845 in total); on auto `D.price` (int) float, `L.big` (long) long, `D.b` (byte) float, `L.mpg` (int) int.
- Format and value label are the base's: `scatter L.volume t` ticks "5,000 … 25,000" under `%12.0fc`; `scatter close D.date` x ticks "02jan1960 … 08jan1960" (a day difference drawn in `%td`, P1.7.5); `scatter L.foreign t, ylabel(, valuelabel)` draws "Domestic", "Foreign" and the title "Car origin, L". `gen double z = L.foreign` carries no value label, so dash attaches it.

### E4. twoway's refusals once operators are accepted (research §2.5, critic c1/c3)

- `sort mpg` then `twoway scatter L.mpg t`: "not sorted" r(5); `gen double z2 = L.mpg` gives the same, so `tsrevar` at build reproduces it.
- Any `by()` with an operated plot variable in any layer: "not sorted" r(5) (`scatter D.close t, by(g)`; xtset panels; `tsline D.close, by(g)`; `(scatter close t) (line D.close t), by(g)`). Plain `tsline close, by(g)` draws.
- Bare `sort` with an operated x: "factor-variable and time-series operators not allowed" then "option sort() incorrectly specified", r(198), on scatter, line, connected, area, bar, spike, dropline, dot, mspline, mband, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter; rc 0 on lfit, qfit, lfitci, qfitci, the five pc types, tsline, tsrline; an operated y with `sort` is always accepted; `sort(L.t)` is "L.t invalid name" r(198) in both already.
- Out of scope: `mlabel(L.make)` (twoway r(111) "variable L not found"), `by(L.foreign)` and `colorvar(L.mpg)` (r(101)); dash refuses all three r(198) "not a time-series expression" (test_help_claims_2.cscript HC2-10d..i; test_option_validation.cscript OV-121, OV-124). `[aw=L.weight]` (twoway rc 0; dash r(198)) is P2.14.
- Already right: `dash scatter close t if L.close > 1300` draws twoway's 33 rows (critic gap 7), because Stata evaluates the qualifier (`_dash_qual_gen`).

### E5. Why the renderer cannot take `L.close` (research §3)

- `_dash_write_data` runs `unab` on its varlist (dash.ado:4544-4545): `unab _dw_vars : `_dw_vars'`.
- `_dash_take_qual_columns` (dash_render.py:27657) refuses every reserved column the spec does not name:

  ```python
  27678     names = _dash_qual_cols_named(spec)
  27679     cols = [str(c) for c in df.columns]
  27680     reserved = [c for c in cols if c.startswith(_DASH_RESERVED_PREFIX)]
  27681     for c in reserved:
  27682         if c not in names:
  27683             raise ValueError(
  ```

  Probe: a frame holding `__dasht1` raises `dash: the data hold a column named '__dasht1'; names beginning with __dash are reserved…`.
- Tooltips admit only Stata names (:27243 `_dash_is_stata_name(_c)`); `L.close` is not one.

So each expression becomes a Stata-named column `__dasht<k>` the spec maps back to its expression and twoway's text. The lifecycle is WP-29 P0.1's (`__dashs<k>`, `_dash_sort_gen`, `_dash_take_sort_columns`) and the qualifier columns' (`__dashq<k>`, `_dash_qual_gen`).

### E6. Text twoway draws (research §2.3, SVG `<text>`)

```
line D.close date (tsset date)  y title "Closing price, D", x title "Date"
line close L.close t            keys "Closing price", "Closing price, L"
scatter L(1/2).close t          keys "Closing price, L", "Closing price, L2"
tsline D.close                  y title "Closing price, D"
line D.y2 t (y2 unlabelled)     "D.y2"
line l.close L1.close DL.close D2.close L0.close t -> "…, L", "…, L", "…, LD", "…, D2", "Closing price"
line S1.close F2.close L2D.close d.l.close t        -> "…, S", "…, F2", "…, L2D", "…, LD"
80-character label + L.         the full 80 characters + ", L" (83, not truncated)
```

### E7. The export blocks (dash.ado)

- `_dash_render_immediate` (:6432): the qualifier rewrite `mata: st_local("json_spec", _dash_qual_rewrite(st_local("_json_orig"), "_dq_err", 1))` (:6524); the empty check `if "`needed_vars'" == "" {` (:6606); `_dash_formats_json "`needed_vars'" _dash_fmt_json _dash_date_vars` (:6696); `if `_dq_n' + `_ds_n' > 0 {` (:6721); `_dash_qual_gen` (:6725) and `_dash_sort_gen` (:6730); `_dash_write_data "`data_json_path'" `needed_vars' `_dash_qual_vars' `_dash_sort_vars'` (:6741); `master_json` (:6769).
- `_dash_prepare_spec` (:7263): the per-graph rewrite beside `_qg_<k>` (:7606); `mata: _dash_extract_vars(`"${dash_json_`gname'}"', "gvars")` (:7619); `all_vars` (:7621), `row_vars` (:7692); `local _novars = ("`all_vars'" == "")` (:7770); the estimates guard (:7869); the export block (:7873-7886); `master_json` (:8049).
- `_dash_qual_gen` (:4773) refuses a user variable named `__dash*` r(110), naming "its qualifier columns __dashq#, its join-order columns __dashs#, …" (:4781); `_dash_sort_gen` (:4910) has the same words.
- R6: these export-block paragraphs are owned in turn by S12, S22, S34 and S42; S34 noted that S42 adds `ts` keys on the same `master_json` lines (section-34 :369, :430).

### E8. The renderer's take-in, labels and CSV (dash_render.py)

- Saved: `DashRenderer._load_data` (:29266) sets `self.variable_labels = _dash_clean_var_labels(stata_json.get("variableLabels", {}))` (:29293), then takes out the sort and qualifier columns.
- Served: the generated app's data load `var_labels = _dash_clean_var_labels(…)` (:34586) and `df, sort_keys = _dash_take_sort_columns(df, spec)` / `df, qual_masks = _dash_take_qual_columns(df, spec)` (:34632-34633), followed by a loop popping each taken column from `var_labels`, `val_label_names`, `type_is_str` and `date_vars`.
- `_dash_csv_meta(columns, formats, string_flags, value_labels, value_label_names, filename=…, storage_types=None)` (:17298) returns `{"columns", "strings", "dates", "labels", "storage", "filename"}`; its callers are `DashRenderer._csv_button` (:32384, saved) and the generated `_send_csv` path (:36200, served). The page writer `_DASH_CSV_JS` (:18349) writes the header as `cols.map((c) => dash_csv_quote(dash_csv_guard(c)))` (:18400).
- Notes that name a plot column: `_dash_load_columns`' format notes (:740 and :763, `f"dash: variable '{col}' has display format …"`) are reachable for a `__dasht<k>` column whose base has a `%21x`-type or unreadable format. `_dash_display` (CRITICAL, 51 call sites) is not edited.
- Copy-list anchors (R2 row S42): constants after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE",` (:32979); functions after `"_dash_qual_cols_named", "_dash_take_qual_columns",` (:33153).

### E9. Help (dash.sthlp)

The "Plot types" paragraph at :243-256 documents the count and string-variable refusals only; nothing documents operators. :233-235 is the tsline synopt ("drawn against the time variable {help tsset} set"). `test/test_help_claims_1.py::TestThePlotTypesSection::test_the_time_series_row_is_twoways_rule` (:435) reads that section.

### E10. Tests that pin today's behaviour

A grep of `test/` at `c96facd` for operator plot varlists (`operators not allowed`, `D.close`, `L.close`, `D.price`, `L.price`) finds only option-variable pins: HC2-10d..i (`test_help_claims_2.cscript:460-464`) and OV-121/OV-124 (`test_option_validation.cscript:698-706`). None changes: option variables are out of scope (E4). 42-01 re-measures; any plot-varlist pin found red is flipped in place with a `Flipped:` line (R9).

### E11. Blast radius (research §6 and critic, index at `c96facd`)

| Symbol | Risk | Action |
|---|---|---|
| `_dash_csv_meta` | CRITICAL (8 processes) | warn; one optional keyword, default unchanged |
| `ServerAppBuilder._generate_app_source` | HIGH | warn; lines added in the data load and `_send_csv` only |
| `ServerAppBuilder._glyph_layer_lines` | HIGH | warn; names appended at S42's anchors |
| `_dash_take_qual_columns` | LOW (+ served codegen) | one keyword `keep` |
| `DashRenderer._load_data` | LOW (+ `ServerAppBuilder._frame`) | lines added |
| `_dash_load_columns` | grep: `_load_data`, the template | one keyword `display_names` |
| dash.ado and Mata programs | UNKNOWN | callers by grep (Risk) |

## User stories

- **US-42.1** As a twoway user with time series, I want `line D.close date`, `tsline D.close`, `lfit close L.close` and `scatter L(1/2).close t` drawn, so a pasted time-series do-file works in dash in the saved page and the served app.
- **US-42.2** As a twoway user, I want operated series computed over all my observations under my `tsset`, with `if`, `in` and filter moves selecting rows, so the values match what twoway draws for the same `if`.
- **US-42.3** As a twoway user, I want titles, keys and tooltips to read `Closing price, D` (or `D.y2` for an unlabelled variable), the base's format and value labels, and my CSV download to head the column `D.close`, never an internal name.
- **US-42.4** As a twoway user, I want dash to refuse what twoway refuses (no `tsset`, a string base, a factor variable, operators on fpfit and the smoothers, `by()` with an operated variable, a bare `sort` with an operated x) in twoway's words and codes.
- **US-42.5** As a dashboard publisher, I want a hand-edited registry that smuggles text into an operator expression refused before Stata runs it.

## Business requirements

- **BR-42.1** `L.`, `F.`, `D.`, `S.`, any combination of them with or without a number, `L(numlist).` and `L.(varlist)` are accepted in the varlist of scatter, line, connected, area, bar, spike, dropline, dot, lfit, qfit, lfitci, qfitci, mspline, mband, rarea, rbar, rspike, rcap, rline, rconnected, rcapsym, rscatter, pcspike, pcarrow, pcbarrow, pcscatter, pccapsym, tsline and tsrline, at any variable position, on the one-line route, `dash build` and `dash serve`.
- **BR-42.2** Each operated series is computed over all observations under the `tsset` in force at build, as `tsrevar` computes it (gaps and panels included), stored in `tsrevar`'s storage type with the base's display format and value label. `if`, `in` and filter moves select rows; they never recompute the series. A computed layer over an operated variable (lfit on L.close) is fitted on the selected rows, as twoway fits it.
- **BR-42.3** Axis titles, legend keys and tooltip labels read twoway's text: the base's label, a comma and a space, and the normalised operator, or the normalised expression when the base has no label; never truncated at 80 characters.
- **BR-42.4** The CSV header and any note naming an operated column show the normalised expression. No page, document, note or download shows `__dasht`.
- **BR-42.5** Refused in twoway's words and codes, before anything is registered or written: no `tsset` (r(111)); a string base (r(109)); a factor variable (r(101)); an unknown operator (r(198)); a missing variable (r(111)); operators on fpfit, fpfitci, lowess, lpoly, lpolyci, histogram and kdensity (r(101)); data not sorted by the time variable at build (r(5) `not sorted`, nothing left behind); `by()` with an operated plot variable in any layer (r(5) `not sorted`, then one dash line saying to generate the variable first); a bare `sort` with an operated x on the 18 types of E4 (r(198), twoway's two lines). An operated y with `sort`, and `sort` on the other types, are accepted.
- **BR-42.6** A graph whose every plot variable is an operator draws on every route.
- **BR-42.7** A user variable named `__dasht<k>` is refused r(110) in words that name the time-series columns; a registry entry that is not an operator expression on an existing variable is refused r(198) and the data are untouched.
- **BR-42.8** The help documents operators, the accepted and refused types, the computation rule, the text rule and the two refusals.

## Technical requirements

### Commit 1: operators drawn

- **TR-42.1 Parsers (dash.ado).**
  - `_dash_parse_varpart_3v` and `_dash_parse_varpart_4v`: `syntax varlist(numeric ts) [if] [in] [aweight fweight pweight iweight]`; the GAPS2 G2 comment gains one sentence (twoway's `ts`, E2).
  - New `_dash_parse_varpart_ts`, directly after `_dash_parse_varpart_std`'s `end`: a copy of `_dash_parse_varpart_std` with `varlist(numeric ts)` and a header comment citing E2. A separate program, so the macro-safe `0` handling JSE-44/46/47/66/69 certify stays untouched.
  - At :3797 the std dispatch becomes `if inlist("`ptype'", "fpfit", "fpfitci", "lowess", "lpoly", "lpolyci") _dash_parse_varpart_std `macval(varpart)'` / `else _dash_parse_varpart_ts `macval(varpart)'`. `_dash_parse_varpart_1v` (histogram, kdensity) is unchanged.
  - Every refusal of E2 then comes from `syntax` in twoway's words; none is typed by hand.
- **TR-42.2 Mata (dash_parse.mata), beside `_dash_sort_*` (after `_dash_sort_export`), with header-index entries (:1-303) in place.**
  - `void _dash_tsop_reset()`: empties the expression table (globals `$dash__tsop_n`, `$dash__tsop_e<k>`, as the sort table keeps its own).
  - `string scalar _dash_tsop_rewrite(string scalar json, string scalar errmacro)`: scans only the plot-variable keys `yvar`, `xvar`, `yvar1`, `yvar2`, `y1var`, `x1var`, `y2var`, `x2var` (never `var`, `mlabel`, `colorvar`, `wexp`, `sortvars`, `if_expr`, `in_expr`); a value holding `.` is an expression; each distinct expression across the dashboard gets `__dasht<k>` (k from 1, in first-seen order); the value is replaced. The canonical rule, checked by a byte loop (no `regexm`, whose engine follows the caller's version): the text splits at its first `.` into an operator part and a base; the operator part is one or more of `L`, `F`, `D`, `S`, each followed by nothing or by 1 to 4 digits not led by `0` (the renderer's `_DASH_TSOP_EXPR_RE` admits the same set); the base must be an existing variable spelled exactly (`_st_varindex(base, 0)` is not missing and `st_varname()` of it equals `base`). The base is not held to ASCII: Stata 14+ names may hold Unicode letters, which twoway accepts and `_dash_is_stata_name` (dash_render.py:1573) admits, and an exact variable name can hold no quote, blank, `;`, `$` or backtick. An expression failing the rule sets `errmacro` to `registry entry <shown> holds a variable dash cannot read` (shown bounded to 80 characters through `_dash_say`'s rules) and returns the json unchanged. More than 9,999 distinct expressions → `errmacro` r(134)'s words.
  - `void _dash_tsop_export()`: the caller's locals `_dts_n` and `_dts_e<k>`, as `_dash_qual_export` fills its own.
  - `string scalar _dash_tsop_meta()`: by value, JSON-escaped (the escaper `_dash_qual_rewrite` uses), `"ts_cols":{"__dasht<k>":{"expr":"L.close","label":"<text>"},…}` and the formats fragment `"__dasht<k>":"<st_varformat(base)>"`. `<text>` = `st_varlabel(base) != "" ? st_varlabel(base) + ", " + <operator part> : <expr>`, read by value so an 80-character label is carried whole (E6).
  - Each of the four is added to dash.ado's `_needed` list (:237) and to `test/program_coverage_map.py` `COVERAGE["dash_parse.mata"]` under S42's anchor (X.5).
- **TR-42.3 `_dash_tsop_gen <cmdname>` (new Stata program, after `_dash_sort_gen`'s `end`, `version 19`).**
  1. `_dts_n == 0` → exit. `"`: char _dta[_TStvar]'" == ""` → `display as error "time variable not set"`, exit 111.
  2. For each k: re-check `_dts_e<k>` against TR-42.2's rule in Mata (a do-file may have edited the globals since the rewrite); then `capture noisily tsrevar `_dts_e`k''`; rc → drop what was made, exit rc (r(5) `not sorted`, r(111), r(109) pass through in Stata's words); `local ty : type `r(varlist)''`; `quietly generate `ty' __dasht`k' = `r(varlist)''`; `format __dasht`k' `: format <base>'`; the base's value label set, if any, by `label values`.
  3. `c_local _dash_tsop_vars` the made names. The expression reaches `tsrevar` only after the regex check, so no other text is ever evaluated.
  - The reserved-prefix messages of `_dash_qual_gen` (:4781) and `_dash_sort_gen` gain "its time-series columns __dasht#" (wording change; commit 2's TSO-10 pins it).
- **TR-42.4 Security (rule 1).** The registry is user-editable globals: every expression is checked twice (rewrite, generation) against the canonical rule (operator bytes, then an exact existing variable name); no expression text is interpolated into a command except after the check, and only as `tsrevar`'s argument; labels and formats reach JSON only through the escaper, by value; Stata messages echo through `_dash_say`; the renderer (TR-42.8) validates names, expressions and label lengths again before using them. A label is bounded at 244 characters in the renderer.
- **TR-42.5 The one-line route (`_dash_render_immediate`, S42's export-block paragraphs, R6).**
  - After the qualifier rewrite (:6524), before `_dash_extract_vars` fills `needed_vars` (:6531-6532): `mata: _dash_tsop_reset()`, `mata: st_local("json_spec", _dash_tsop_rewrite(st_local("json_spec"), "_dts_err"))`, refuse `_dts_err` r(198) via `_dash_say`, `mata: _dash_tsop_export()`. `_dash_extract_vars` then reads the rewritten json, so `needed_vars` holds the `__dasht<k>` names, which do not exist until `_dash_tsop_gen` runs (:6730): remove them from `needed_vars` right after :6583 (`local needed_vars : list needed_vars - _dts_names`, with `_dts_names` the `__dasht1 … __dasht<_dts_n>` list), so `_dash_formats_json` (:6696) and the cell cap never see them; they reach the writer through `_dash_tsop_vars`.
  - The empty check (:6606) counts `_dts_n`: `if "`needed_vars'" == "" & `_dts_n' == 0`.
  - `_dash_fmt_json` (:6696) gains the meta's formats fragment; `_dash_cell_cap` counts `_dts_n` beside `_dq_n + _ds_n`; the estimates guard (:6721) reads `_dq_n' + `_ds_n' + `_dts_n' > 0`.
  - `_dash_tsop_gen` runs after `_dash_sort_gen` (:6730), under the same `capture noisily` and cleanup; its columns join `_dash_write_data` (:6741) and are dropped with the qualifier and sort columns on every exit path.
  - `master_json` (:6769) gains `"ts_cols":{…}` from `_dash_tsop_meta()` after the `sort_cols` pair, on the line S34 extended (keep S34's `scheme_dirs` pair).
- **TR-42.6 The build and serve route (`_dash_prepare_spec`).**
  - The per-graph rewrite beside `_qg_<k>` (:7606) rewrites each graph's json once, after the qualifier rewrite, with the dashboard-wide table (`_dash_tsop_reset` once before the graph loop).
  - `gvars` (:7619) is read from the rewritten graph json, less the `__dasht<k>` names, so `all_vars` (:7621) and `row_vars` (:7692) hold only variables (critic gap 2).
  - `_novars` (:7770) counts `_dts_n`; the estimates guard (:7869) and the export block (:7873-7886) as TR-42.5; `master_json` (:8049) gains `"ts_cols":…` after `sort_cols`. `dash serve` inherits through `_dash_prepare_spec`.
- **TR-42.7 Order.** `_dash_tsop_gen` runs after `_dash_qual_gen` (whose `__dash*` clash check runs first) and `_dash_sort_gen`; `_dash_sort_gen` and the by() helper `_dash_qual_gen_by` are `sortpreserve` (`_dash_qual_gen` itself is not, dash.ado:4773, and sorts nothing), which restores `: sortedby` (critic c1: sortedby `t` before and after), so `tsrevar` sees the user's sort.
- **TR-42.8 Renderer take-in (dash_render.py).**
  - Constants after `_DASH_QUAL_NAME_RE` (:27608): `_DASH_TSOP_PREFIX = "__dasht"`, `_DASH_TSOP_NAME_RE = re.compile(r"__dasht[1-9][0-9]{0,3}\Z")`, `_DASH_TSOP_EXPR_RE = re.compile(r"(?:[LFDS][1-9][0-9]{0,3}|[LFDS])+\.(?P<base>\S{1,32})\Z")`, `_DASH_TSOP_LABEL_MAX = 244`.
  - `_dash_tsop_cols_named(spec) -> dict[str, dict]` after `_dash_qual_cols_named`: `build_options.ts_cols`, each key fullmatching the name rule, each value a dict whose `expr` fullmatches the expression rule with `_dash_is_stata_name(m.group("base"))` true (Unicode letters admitted, as Stata admits them) and whose `label` is a `str` of at most 244 characters; anything else raises `ValueError("dash: the spec's ts_cols entry … is not one dash writes.")`. No entry → `{}`.
  - `_dash_take_tsop_columns(df, spec) -> tuple[pd.DataFrame, dict]`: each named column must be in `df` and numeric (`pd.api.types.is_numeric_dtype`), else `ValueError`; it returns `df` unchanged and the map.
  - `_dash_take_qual_columns(df, spec, keep=())`: a reserved column in `keep` is neither refused nor dropped; every other rule unchanged. Its docstring names the time-series columns.
  - `_dash_tsop_labels(variable_labels, tsmap) -> dict`: a copy of `variable_labels` with each `__dasht<k>` set to its `label`.
- **TR-42.9 Both modes.**
  - Saved, `DashRenderer._load_data`: after the sort take-out, `self.df, self.tsop_cols = _dash_take_tsop_columns(self.df, self.spec)`; the qualifier take-out passes `keep=tuple(self.tsop_cols)`; after `variable_labels` (:29293), `self.variable_labels = _dash_tsop_labels(self.variable_labels, self.tsop_cols)`. `ServerAppBuilder._frame` inherits it.
  - Served, `_generate_app_source` (HIGH, warn): the data load gains, before `_dash_take_qual_columns` (:34633), `df, _tsop_cols = _dash_take_tsop_columns(df, spec)`, passes `keep=tuple(_tsop_cols)` to the qualifier take-out, and after it `var_labels = _dash_tsop_labels(var_labels, _tsop_cols)`. The pop loop is not extended (ts columns are data).
  - Formats come through the spec's formats map, so `_dash_load_columns` makes `L.date` a date column (S35's axis) and S18 writes `%12.0fc` tick text; value labels come with the data; storage types come from the writer.
  - Keys, titles and tooltips then read twoway's text through S19's `_dash_layer_series`, `_dash_axis_default_titles` and the tooltip label reader, unedited.
- **TR-42.10 Filter moves: no code.** A ts column is a data column fixed at build: the saved `_FILTER_JS` copies its rows from the snapshot; the served redraw selects rows of `df` and refits computed layers over them (BR-42.2). Tests pin both.
- **TR-42.11 Copy lists (R2 row S42).** Constants, after `"_DASH_QUAL_PREFIX", "_DASH_QUAL_NAME_RE",` (:32979): `"_DASH_TSOP_PREFIX", "_DASH_TSOP_NAME_RE", "_DASH_TSOP_EXPR_RE", "_DASH_TSOP_LABEL_MAX",`. Functions, after `"_dash_qual_cols_named", "_dash_take_qual_columns",` (:33153): `"_dash_tsop_cols_named", "_dash_take_tsop_columns", "_dash_tsop_labels",` (commit 2 adds `"_dash_col_display",` after them).
- **TR-42.12 JS twins: none in commit 1.** The ts columns are ordinary source columns.
- **TR-42.13 Registries (commit 1).** `test/function_test_map.py` under S42's anchor, alphabetical: `'_dash_take_tsop_columns'`, `'_dash_tsop_cols_named'`, `'_dash_tsop_labels'`, each naming its `test/test_ts_operators.py` node. `test/program_coverage_map.py` `COVERAGE["dash.ado"]` under S42's anchor: `"_dash_parse_varpart_ts": ("test_parser.cscript:TSO-01", "test_parser.cscript:TSO-04")`, `"_dash_tsop_gen": ("test_parser.cscript:TSO-06", "test_parser.cscript:TSO-11")`; `COVERAGE["dash_parse.mata"]` the four Mata functions (TSO-01, TSO-11).
- **TR-42.14 Help (commit 1)**, dash.sthlp "Plot types" (R3, S42's) after the string-variable sentences (:250): one paragraph: operators accepted where twoway accepts them (the type list of BR-42.1), refused in twoway's words on fpfit, fpfitci, lowess, lpoly, lpolyci, histogram and kdensity; computed by Stata at build under the `tsset` then in force over all observations, so `if`, `in` and filter moves select rows; stored in `tsrevar`'s type with the base's format and value labels (a `D.` of a date is drawn as a date, as twoway draws it); titles and keys read "label, OP"; refusals of no `tsset`, string and factor variables. "Syntax, Description" (:45-207, S42's) gains one example: `sysuse sp500`, `tsset date`, `dash line D.close date`. Lines at most 79 characters.

### Commit 2: twoway's refusals and display names

- **TR-42.15 `by()` (dash.ado `_dash_plot`).** `_dash_process_segment` returns `r(hasts)` = 1 when any plot variable of the segment (every y of a multi-y segment, x, and the range/pc variables) holds `.`; `_dash_plot` gathers it beside `_byq_vv_<k>` (around :5210). When the graph has `by()` and any segment has it: `display as error "not sorted"`, then `display as text "dash: twoway refuses by() with a time-series operator in a plot variable; generate the variable first, for example: generate double dclose = D.close"` (the example built from the first operated expression through `_dash_say`), exit 5, before anything is registered.
- **TR-42.16 Bare `sort` (`_dash_process_segment`).** Once x is known, if `s(sort)` is the bare form (dash.ado :1209), `ptype` is one of E4's 18 types and x holds `.`: `display as error "factor-variable and time-series operators not allowed"`, `display as error "option sort() incorrectly specified"`, exit 198.
- **TR-42.17 CSV header (`_dash_csv_meta`, CRITICAL, warn).** New keyword `display_names=None`: when a dict, the result gains `"headers": {c: display_names[c] for c in cols if c in display_names}` (str values only); absent → no key, today's result byte for byte. Callers: `DashRenderer._csv_button` (:32384) passes `display_names={k: v["expr"] for k, v in getattr(self, "tsop_cols", {}).items()}`; the generated `_send_csv` call (:36200) passes the same from `_tsop_cols`. JS twin, `_DASH_CSV_JS`'s header line (:18400): `cols.map((c) => dash_csv_quote(dash_csv_guard((meta.headers && Object.prototype.hasOwnProperty.call(meta.headers, c)) ? meta.headers[c] : c)))`. The expression rule admits no CSV formula lead (`=`, `+`, `-`, `@`), and `dash_csv_guard` still runs.
- **TR-42.18 Note display names.** `_dash_col_display(name, names=None)` after `_dash_tsop_labels`: `names[name]` when `name` is a key of `names`, else `name`. `_dash_load_columns` gains `display_names=None`, used at its two format notes (:740, :763) through `_dash_col_display`; `_load_data` (:29321) and the template's `_dash_load_columns` call (:34624) pass the expression map. Both calls run before the take-outs (:29335, :34632), so the map is read from the spec there, `{k: v["expr"] for k, v in _dash_tsop_cols_named(spec).items()}`, which validates it as the take-out will. 42-16 re-greps every `_dash_display(` site and `f"dash:…{col…}"` note at the base for a plot-column argument and routes any it finds the same way, listing them in the commit body.
- **TR-42.19 Registries and help (commit 2).** `'_dash_col_display'` under S42's anchor. Help: the operator paragraph gains the `by()` and bare-`sort` refusals in twoway's words and "the CSV column is headed by the expression".

## Boundaries

- **Batch 15 partners.** S43: `_apply_marker_opts`, `_apply_line_opts`, `_apply_mlabel_opts`, `_apply_fill_opts`, the colour mappers, `_textbox_color`, `_dash_graph_color`, `_resolve_kpi_color`, `_dash_refline_draw`, `_dash_apply_axis_spec`, `_dash_apply_scale_look`, `OptionTranslator.stata_colour`; help "Marker and Transparency Options". S44: `_dash_apply_axis_options`, `_dash_finish_secondary_axes`, `_dash_count_axes`, `_dash_axis_count_ticks`, the `_dash_ts_*` model, `_DASH_AXIS_FINISH_JS`; help "Axis and Display Options". S42 touches none of them; neither edits a file of S42's except `dash_render.py` (distinct functions) and dash.sthlp (distinct titles).
- **Earlier sections, read only:** S19's helpers, S18's tick formats, S35's date axes, S12/S22/S34's export-block paragraphs (S42 adds its own lines beside them).
- **Not this section's:** operators in option variables (`mlabel()`, `colorvar()`, `by()`, `hover()`, `filter()`); `[aw=L.x]` (P2.14); moving working columns to a temporary frame (P2.28: `_dash_tsop_gen` must then still run in the user's frame first); `mlabel(L.make)`'s r(111) words.
- **Never:** `_dash_display`, `_dash_warn_once`, `_dash_layer_series`, `_dash_axis_default_titles`, `_dash_legend_key`, `_make_figure_body`, `_FILTER_JS`.

## Stata truth

### `scripts/extract_ts_operator_truth.do` → `test/fixtures/ts_operator_truth.json` (commit 1)

S02's stanza (TR-02.9), then `adopath ++ "`repo'/"` and `global dash_nobrowser 1`; `_meta` as `scripts/extract_series_label_truth.do` (S19) writes it: `stata_version`, `born_date`, `dash_commit` (`git rev-parse HEAD` captured by `shell` into a local, read through `Macro.getLocal`), `extracted`; the python block never calls Stata, uses no `shell=True`, writes a backtick as `\x60`. Each probe runs `capture noisily` inside a named log; SVGs are read only through `scripts/svg_truth.py`; values come from `serset use`.

- **Data:** `sysuse sp500, clear`; `gen t = _n`; `format volume %12.0fc`; `format close %9.2f`; `gen y2 = close` (no label); `gen float xf = close/7`; `gen double xd = close/7`; a 2 × 10 `xtset` frame (`id`, `tt`, `y`); auto for `L.foreign` with its value label and the storage-type cases.
- **Probes (rc, error lines, serset values, SVG title/key/label text, serset storage type):** every type of E2 with `D.close L.close` (range `L.low L.high t`, pc `L.close L.t close t`); `L(1/2).`, `LD.`, `S2.`, `F.`, `L0.`, lower case; `tsset date` (gaps) and `tsset t`; the xtset panel; `D.y2` unlabelled, an 80-character label, a label of blanks; `L.foreign` with `ylabel(, valuelabel)`; `L.volume` (`%12.0fc`), `D.date` (`%td`); `scatter D.close t if t>5 & t<9`; `lfit close L.close if t>100`; the refusal matrix (no tsset, `L.make`, `i.foreign`, `X.mpg`, `L.nosuch`, the seven refused types, unsorted data); `by(g)` with an operated variable in each form of E4; bare `sort` with an operated x on all 29 accepting types and with an operated y.
- **Records:** per probe `cmd`, `rc`, `err` (the error lines), `values` (per serset variable, `.` as null), `types`, `texts`; `_meta.data` holds the subsets the tests rebuild.
- Run: `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_ts_operator_truth.do"`; `git add -f test/fixtures/ts_operator_truth.json`.

### Area cases, `test/test_parser.cscript` (R1; one contiguous run after LB-43's block, whose last line is `macro drop lb_pfail` (:2850 at `c96facd`), before `capture erase "`c(tmpdir)'dash_p1a_run.log"`)

Each case compares live twoway (`capture twoway … nodraw`, rc and first error line from a log) with dash through the script's `_p1a_vs_tw` helper or its `bad`/`exit 9` pattern, printing `TSO-nn PASS: …`.
- **TSO-01..03** (commit 1): `line D.close date`, `tsline D.close`, `lfit close L.close` rc 0 on the one-line route; the spec's `ts_cols` maps `__dasht1` to `D.close` and `Closing price, D`.
- **TSO-04:** every accepting type rc 0; the seven refused types r(101) with twoway's line.
- **TSO-05:** no tsset r(111); `L.make` r(109); `i.foreign` r(101); `X.mpg` r(198); `L.nosuch` r(111); each line equal to twoway's.
- **TSO-06:** data sorted otherwise at build r(5) `not sorted`; afterwards `capture unab x : __dash*` is r(111), `c(changed)` and `: sortedby` unchanged; tsset cleared after registration gives r(111) at build.
- **TSO-08:** the one-line route, `dash build` and `_dash_serve_spec` write the same spec `ts_cols` and the same exported column.
- **TSO-09:** storage follows `tsrevar` (`D.xf` float, `L.mpg` int); format and value label are the base's; the 80-character label is carried whole in the spec.
- **TSO-11** (security): `"yvar":"L.close;drop _all"` and `"yvar":"X.close"` written into `$dash_json_<g>` by hand → r(198), `c(N)` and `c(k)` unchanged.
- **TSO-12:** `[aw=L.weight]` stays r(198) (P2.14's pin).
- **TSO-13:** `dash scatter D.close LD.close` and `dash lfit D.close L.close` draw on the one-line route and through `dash build`.
- **TSO-14:** `dash scatter close t if L.close > 1300` keeps twoway's 33 rows (a guard).
- **TSO-07** (commit 2): `by(g)` with an operated variable r(5) on each form of E4 and every route, the dash hint line second; bare `sort` with an operated x r(198) with both lines on the 18 types, rc 0 on the others and with an operated y.
- **TSO-10** (commit 2): a user variable `__dasht1` r(110), the message naming `__dasht#`.

### The S42 block of `test/test_wp30_truth.cscript` (R1)

Helpers `_s42_*` directly above S01's `* ==== S42 P1.7: Time-series operators in plot varlists ====` header (a `python:` reader of a saved page's document JSON: titles, legend items, tooltip labels, the column values of the first glyph's source; any Stata helper declares `version 19`). Cases report through `_w30_expect`/`_w30_done`, write pages and SVGs only under `` `w30_work' `` and erase them before the `S42 end` line (TR-01.10 item 4); run alone (`WP30_ONLY=S42`) the block prints its PASS lines and `ALL CHECKS PASSED`.
- **TSO-20:** `line D.close date`: dash's saved y title equals twoway's SVG text; the drawn D.close values equal the serset to 0.
- **TSO-21:** `scatter L(1/2).close t`: both keys equal twoway's.
- **TSO-22:** `scatter D.close t if t>5 & t<9`: row t = 6 holds 4.940063.
- **TSO-23:** the xtset panel: missing L.y at each panel start.
- **TSO-24:** `scatter close D.date`: the x axis is a date axis (P1.7.5).

## TDD test stubs

### Commit 1, new `test/test_ts_operators.py` (red at the batch-15 base unless marked guard; 42-01)

Module docstring: the defect (Overview), E2-E6, the fixture. `_FIX = json.load(test/fixtures/ts_operator_truth.json)`; `_frame()` builds the fixture's sp500 rows plus `__dasht1`/`__dasht2` columns from its serset values; `_spec(plots, ts_cols)` builds a spec with `build_options.ts_cols` and the formats map; both modes render through the helpers `test/test_join_order.py` uses for its `__dashs1` frames (saved `DashRenderer`, served `_served`), and moves through `test_saved_filter_layers._move` and `test_served_filter_move._move`.

- Test: the fixture is stamped (four `_meta` keys, `stata_version` starting `19.`) and holds every probe id — `TestTheFixture::test_it_is_stamped`
- Test: dash.ado declares `varlist(numeric ts)` in `_dash_parse_varpart_3v`, `_4v` and `_ts`; the dispatch keeps `_std` for the five types — `TestTheParsers::test_ts_is_declared_where_twoway_declares_it`
- Test: `_dash_tsop_cols_named` accepts the fixture's map and a Unicode base (`L.prixé`); refuses `__dasht0`, `__dashtx`, `__dasht12345`, an expr `L.close;drop`, `X.close`, `L.1x`, `L.a b`, `L00.close`, a 245-character label, a non-str label, a list — `TestTheColumnsAreNamedInTheSpec::test_the_map_rule`
- Test: `_dash_take_tsop_columns` keeps a named numeric column; refuses one missing or of strings — `TestTakingTheColumnsIn::test_the_take_rule`
- Test: `_dash_take_qual_columns(df, spec, keep=("__dasht1",))` keeps it; an unnamed `__dasht2` is still refused — `::test_the_qualifier_gate_still_refuses_others`
- Test: `ServerAppBuilder._frame` on data with a bad `ts_cols` raises at build — `::test_served_build_refuses_a_bad_map`
- Test: `_dash_tsop_labels` sets each name's label and copies the dict — `TestTheLabels::test_the_label_rule`
- Test (both modes, fixture): line D.close date, tsline D.close, scatter close L.close, scatter L(1/2).close t, line D.y2 t, the 80-character label: axis titles and keys equal the fixture's SVG text — `TestTheLabelsAreTwowaysText::test_case[<probe>-saved|served]`
- Test (both modes): the tooltip label of a ts column is twoway's text — `::test_tooltips[saved|served]`
- Test (both modes, fixture): drawn values for line, tsline, rarea, pcspike and lfit equal the serset — `TestBothModesDrawTheSameValues::test_case[<type>-saved|served]`
- Test (both modes): `L.date` and `D.date` draw a date axis; `L.volume` keeps `%12.0fc` — `TestTheBaseFormat::test_case[<probe>-saved|served]`
- Test (both modes): `L.foreign` with `ylabel(, valuelabel)` draws "Domestic", "Foreign" — `TestTheBaseValueLabel::test_case[saved|served]`
- Test (node, saved): after each `_MOVES` move the drawn D.close values at the kept rows equal the fixture's `if` values — `TestAFilterMoveKeepsTheComputedSeries::test_saved[<move>]`
- Test (served): after a range move D.close at the kept rows equals the fixture; lfit over L.close equals twoway's `lfit … if t>100` — `::test_served[line|lfit]`
- Test: the generated app, executed, defines the three helpers and the four constants — `TestTheServedCopy::test_the_app_defines_the_names`
- Test: dash.sthlp's "Plot types" names operators, the 29 types and the seven refused, and the example — `TestTheHelp::test_the_help_documents_operators`
- Guard: a graph with no ts column renders byte for byte as at the base (the single-y page digest unchanged) — `TestNoOperatorNoChange::test_the_page_is_unchanged`
- Help claim, `test/test_help_claims_1.py`: `TestThePlotTypesSection::test_the_operator_paragraph_is_twoways_rule` (operators accepted on the twoway list; refused types named; "not sorted"; "time variable not set").
- Test (cscript): TSO-01..TSO-06, TSO-08, TSO-09, TSO-11..TSO-14; TSO-20..TSO-24.
- Shared: `test/test_saved_filter_layers.py` `_CORPUS` is not edited (it has no ts frame); the move tests live in this file.

### Commit 2 (red on the tree commit 1 left; 42-13)

- Test: `_dash_csv_meta(…, display_names={"__dasht1": "D.close"})["headers"] == {"__dasht1": "D.close"}`; without the keyword the result equals the base's for the cases of `test/test_export.py` and `test/test_display_format_sites.py` — `TestTheCsv::test_the_meta_carries_headers`
- Test (node, saved) and served: the CSV's first line holds `D.close`, never `__dasht` — `TestTheCsv::test_the_header_is_the_expression[saved|served]`
- Test: `_dash_col_display` — `TestTheNotes::test_the_display_rule`
- Test (both modes): a base with format `%21x` → the note names `D.close`; the page text, document JSON titles, legends and tooltip labels hold no `__dasht` — `TestTheTsColumnNamesNeverReachTheUser::test_case[saved|served]`
- Test: dash.ado's `_dash_plot` refusal and `_dash_process_segment`'s sort refusal exist with twoway's words — `TestTheRefusals::test_the_words_are_twoways`
- Test (cscript): TSO-07, TSO-10.

### Pinned tests to flip (R9)

None found at `c96facd` (E10). 42-01 runs the existing varlist cscripts (`test_parser.cscript`, `test_adversarial.cscript`, `test_option_validation.cscript`) on the base and records any plot-varlist operator pin; such a pin is flipped in 42-11 with `Flipped: <node> -- r(101) for an operated plot variable was wrong because twoway draws it`.

## Test plan

| What | How | Fixture / data | Both modes? |
|---|---|---|---|
| Parsers and refusals | cscript TSO-04, TSO-05, TSO-07; pytest `TestTheParsers`, `TestTheRefusals` | sp500, auto | n/a |
| Registry, generation, security | cscript TSO-06, TSO-08, TSO-09, TSO-10, TSO-11, TSO-13 | sp500 | n/a |
| Take-in and gate | pytest `TestTheColumnsAreNamedInTheSpec`, `TestTakingTheColumnsIn` | literal frames | yes (served build) |
| Text, values, formats | pytest `TestTheLabelsAreTwowaysText`, `TestBothModesDrawTheSameValues`, `TestTheBaseFormat`, `TestTheBaseValueLabel`; cscript TSO-20..TSO-24 | `ts_operator_truth.json` | yes |
| After moves | pytest `TestAFilterMoveKeepsTheComputedSeries` (node saved; served) | fixture | yes |
| CSV and notes | pytest `TestTheCsv`, `TestTheTsColumnNamesNeverReachTheUser` | fixture | yes |
| Served wiring | `TestTheServedCopy`; G4 guards | generated app | served |
| Help | `TestTheHelp`, `test_help_claims_1.py` | dash.sthlp | n/a |
| Registries, tracking | `test_function_test_map.py`, `test_program_coverage_map.py`, `test_file_headers.py`, `test_cscript_hygiene.py`, `test_tracking_documents.py`, `test_fixtures_are_committed.py` | — | n/a |

**Acceptance criteria.**
- **AC-42.1** (BR-42.1, BR-42.6) TSO-01..TSO-04 and TSO-13 PASS against live twoway; `TestBothModesDrawTheSameValues` passes in both modes.
- **AC-42.2** (BR-42.2) TSO-22, TSO-23 PASS; `TestAFilterMoveKeepsTheComputedSeries` passes, the node test not skipped.
- **AC-42.3** (BR-42.3) `TestTheLabelsAreTwowaysText`, `TestTheBaseFormat`, `TestTheBaseValueLabel`, TSO-20, TSO-21, TSO-24 pass.
- **AC-42.4** (BR-42.4) `TestTheCsv` and `TestTheTsColumnNamesNeverReachTheUser` pass in both modes.
- **AC-42.5** (BR-42.5, BR-42.7) TSO-05..TSO-07, TSO-10, TSO-11 PASS, each error line equal to twoway's.
- **AC-42.6** (BR-42.8) `TestTheHelp` and the help-claim test pass; every changed help line is at most 79 characters.
- **AC-42.7** The full suite through the queue reports 0 failed before each commit; G4 and G7 hold; `test_mode_parity.py` is green and untouched.

## Tasks

**Commit boundary.** Tasks 42-01 to 42-12 form commit 1, made by 42-12 on `wp30-s42` with the subject `Draw time-series operators in plot varlists, part 1 of 2: operators drawn (WP-30 P1.7)`; it leaves the BUGS.md entry, its `WP30_OPEN` key and both markers in place (A156). Tasks 42-13 to 42-18 form commit 2, made by 42-18 with the subject `Refuse and name time-series operators as twoway does, part 2 of 2: by(), sort and display names (WP-30 P1.7)`; it closes all three. `<scratch>` is the orchestrator's WP-30 scratch directory (index.md "Deltas"), which holds `batch-15-base.txt`, `batch-15-impact.txt` and `full_suite_queue.sh`; `$S` is `<scratch>/s42` (42-01 runs `mkdir -p "$S"`), so the logs of S42, S43 and S44, which run in parallel, never share a name or a slot directory; `$WT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp30-s42`, `$SLOT` is `/Users/billy/Desktop/Programs/StataPrograms/d/dash/scripts/stata_slot.sh`. A cscript runs through the driver: `printf 'cd "%s/test"\ndo "%s/test/%s"\n' "$WT" "$WT" "<script>.cscript" > "$S/run_<script>.do"`, then `WP30_ONLY=S42 "$SLOT" "$S" "$S/run_<script>.do"` (log `$S/run_<script>.log`). Each task appends the files it changed to `$S/42-files-<k>.txt`.

<task type="auto" id="42-01">
  <name>Write the fixture and pytest regressions</name>
  <files>scripts/extract_ts_operator_truth.do, test/test_ts_operators.py</files>
  <action><![CDATA[
    Check `git -C "$WT" rev-parse HEAD` equals `cat "<scratch>/batch-15-base.txt"` and `git -C "$WT" branch --show-current` prints `wp30-s42`; stop otherwise. `mkdir -p "$S"`. Create `scripts/extract_ts_operator_truth.do` exactly as "Stata truth" describes (S02's stanza, the data, the probes, named logs, `serset use`, `scripts/svg_truth.py`, S19's `_meta` form) and run it with `DASH_REPO="$WT" "$SLOT" "$S" "$WT/scripts/extract_ts_operator_truth.do"`; it writes `test/fixtures/ts_operator_truth.json`. Create `test/test_ts_operators.py` with every commit-1 stub of "TDD test stubs", naming `dr._dash_tsop_cols_named`, `dr._dash_take_tsop_columns`, `dr._dash_tsop_labels` and `dr._DASH_TSOP_PREFIX` so they fail with AttributeError now. Run `python3 -m pytest test/test_ts_operators.py -q -n 6 -p no:cacheprovider -rf > "$S/42-new-1.log" 2>&1`. Run `test_parser.cscript`, `test_adversarial.cscript` and `test_option_validation.cscript` through the driver and grep their logs for an operated plot varlist pinned at r(101) (E10). Write `$S/42-P1.7-1-failure.txt`: the base sha, one line per failing node, then "Guards (pass at the base)", then any pin found. Edit no shipped file; do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json; d=json.load(open('$WT/test/fixtures/ts_operator_truth.json')); m=d['_meta']; print(all(k in m for k in ('stata_version','born_date','dash_commit','extracted')), m['stata_version'][:3])"` prints `True 19.`; `grep -c FAILED "$S/42-new-1.log"` is at least 20; `git -C "$WT" diff --name-only -- dash.ado dash_parse.mata dash_render.py` prints nothing.]]></verify>
  <done>The twoway operator fixture existed and every commit-1 pytest regression test was shown failing on the unmodified tree, with the failure text saved.</done>
</task>

<task type="auto" id="42-02">
  <name>Write the area and truth cases</name>
  <files>test/test_parser.cscript, test/test_wp30_truth.cscript, test/test_help_claims_1.py</files>
  <action><![CDATA[
    In `test/test_parser.cscript`, after LB-43's block (its last line `macro drop lb_pfail`, :2850 at c96facd) and before `capture erase "`c(tmpdir)'dash_p1a_run.log"`, add one contiguous run headed `// TSO: time-series operators in plot varlists (WP-30 P1.7)` with its data lines and TSO-01..TSO-06, TSO-08, TSO-09, TSO-11..TSO-14 of "Stata truth", each comparing live twoway's rc and first error line with dash's through `_p1a_vs_tw` or the script's `bad`/`exit 9` form. In `test/test_wp30_truth.cscript` put the `_s42_*` helpers directly above S01's `* ==== S42 P1.7: …` header and TSO-20..TSO-24 between S01's S42 start and end lines. Add `TestThePlotTypesSection::test_the_operator_paragraph_is_twoways_rule` to `test/test_help_claims_1.py`, beside `test_the_time_series_row_is_twoways_rule`, reading S02's constants as they stand. Run both scripts through the driver and the new pytest node; append every `TSO-nn FAIL` line and the twoway line it quotes, and the pytest failure, to `$S/42-P1.7-1-failure.txt`, with TSO-12 and TSO-14 under the guards. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -cE "TSO-(0[1-6]|0[89]|1[13]) FAIL" "$S/run_test_parser.log"` is at least 8; `grep -cE "TSO-1[24] PASS" "$S/run_test_parser.log"` prints 2; `grep -cE "TSO-2[0-4] FAIL" "$S/run_test_wp30_truth.log"` is at least 4; `grep -c "LB-43 PASS" "$S/run_test_parser.log"` prints 1.]]></verify>
  <done>The area refusals, the live twoway comparisons and the help claim were in place and shown failing on the unmodified tree, with the guards passing.</done>
</task>

<task type="auto" id="42-03">
  <name>Accept operators in the varpart parsers</name>
  <files>dash.ado</files>
  <action><![CDATA[
    The parsers and `_dash_process_segment` are UNKNOWN to the index; confirm their calls by `grep -n "_dash_parse_varpart_" dash.ado` (expected :3595, :3601, :3652, :3674, :3797 at c96facd) and record them in `$S/42-impact.txt`. Apply TR-42.1: `varlist(numeric ts)` in `_dash_parse_varpart_3v` and `_dash_parse_varpart_4v`; `_dash_parse_varpart_ts` as a copy of `_dash_parse_varpart_std` with `ts`, directly after its `end`, `version 19`, with a header comment citing E2; the dispatch at the std call keeping `_dash_parse_varpart_std` for fpfit, fpfitci, lowess, lpoly and lpolyci. Edit no other line of the parsers and leave `_dash_parse_varpart_1v` alone.
  ]]></action>
  <verify><![CDATA[`test_parser.cscript` through the driver prints `TSO-05 PASS` (the refusals come from `syntax` alone; TSO-04's accepted types need the export of 42-06 and are verified there); `grep -c "varlist(numeric ts)" "$WT/dash.ado"` prints 3.]]></verify>
  <done>dash.ado's parsers accepted operators where twoway does and refused them elsewhere in twoway's words.</done>
</task>

<task type="auto" id="42-04">
  <name>Add the Mata rewrite and export</name>
  <files>dash_parse.mata, dash.ado, test/program_coverage_map.py</files>
  <action><![CDATA[
    Apply TR-42.2: `_dash_tsop_reset`, `_dash_tsop_rewrite`, `_dash_tsop_export` and `_dash_tsop_meta` directly after `_dash_sort_export`, each with a comment block in the file's form, the canonical rule as a byte loop (no `regexm`) and the exact-name `_st_varindex` check, labels and formats escaped by value with the escaper `_dash_qual_rewrite` uses; one header-index entry each in `dash_parse.mata:1-303` after `_dash_sort_export()`'s. Add the four names to dash.ado's `_needed` list (:237). Add their `COVERAGE["dash_parse.mata"]` entries under S42's anchor of `test/program_coverage_map.py`, alphabetically (TR-42.13).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_file_headers.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` reports 0 failed; a scratch do-file `$S/42-mata.do` (`adopath ++ "$WT/"`, `global dash_nobrowser 1`, `sysuse sp500`, `tsset date`, `mata: _dash_tsop_reset()`, then `mata: _dash_tsop_rewrite(` on `{"type":"line","yvar":"D.close","xvar":"date"}` and on `{"yvar":"L.close;drop _all"}`) run through the slot prints `"yvar":"__dasht1"` and a non-empty error macro for the second.]]></verify>
  <done>Mata rewrote plot-variable expressions to __dasht columns, refused anything but a canonical operator on an existing variable, and exported the table and twoway's text.</done>
</task>

<task type="auto" id="42-05">
  <name>Generate the columns in Stata</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Add `_dash_tsop_gen` after `_dash_sort_gen`'s `end` exactly as TR-42.3 specifies (`version 19`; the tsset check; the second regex check in Mata; `tsrevar` under `capture noisily`; `tsrevar`'s storage type; the base's format and value label; dropping what was made on any error; `c_local _dash_tsop_vars`), with a header comment citing E3 and E4. Extend the reserved-prefix messages of `_dash_qual_gen` (:4781) and `_dash_sort_gen` to name "its time-series columns __dasht#". Echo every value through `_dash_say`.
  ]]></action>
  <verify><![CDATA[`$S/42-mata.do` extended to call `_dash_tsop_export` and `_dash_tsop_gen dash` prints `float __dasht1` for `D.xf` and `%9.2f` for `D.close`'s format; on data sorted by `close` it exits 5 with `not sorted` and `capture unab x : __dash*` is then r(111).]]></verify>
  <done>Stata computed each expression into a __dasht column of tsrevar's type with the base's format and value label, cleaning up on every error.</done>
</task>

<task type="auto" id="42-06">
  <name>Wire the one-line export block</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_render_immediate` apply TR-42.5 as S42's own paragraphs (R6): the rewrite after the qualifier rewrite (:6524) with its r(198) refusal; `needed_vars` less the expressions; the empty check (:6606) counting `_dts_n`; the formats fragment into `_dash_fmt_json`; `_dash_cell_cap` and the estimates guard (:6721) counting `_dts_n`; `_dash_tsop_gen` after `_dash_sort_gen` (:6730) inside the same capture and cleanup; its columns into `_dash_write_data` (:6741) and dropped with the others on every exit; `"ts_cols":` after the `sort_cols` pair of `master_json` (:6769), keeping S34's `scheme_dirs`. Edit no line S12, S22 or S34 own.
  ]]></action>
  <verify><![CDATA[`test_parser.cscript` through the driver prints `TSO-01 PASS` to `TSO-04 PASS`, `TSO-06 PASS`, `TSO-09 PASS`, `TSO-11 PASS` and `TSO-13 PASS` (the one-line legs); `test_qualifier_in_stata.cscript` through the driver prints its `ALL` line.]]></verify>
  <done>The one-line route registered, computed, exported and cleaned up operator columns, and a graph of operators alone drew.</done>
</task>

<task type="auto" id="42-07">
  <name>Wire the build and serve block</name>
  <files>dash.ado</files>
  <action><![CDATA[
    In `_dash_prepare_spec` apply TR-42.6 as S42's own paragraphs: `_dash_tsop_reset` once before the graph loop; each graph's rewrite beside `_qg_<k>` (:7606) after the qualifier rewrite; `gvars` (:7619) read from the rewritten json less the `__dasht` names; `_novars` (:7770) and the estimates guard (:7869) counting `_dts_n`; the export block (:7873-7886) generating, writing and dropping the columns; `"ts_cols":` after `sort_cols` in `master_json` (:8049). `dash serve` reaches it through `_dash_prepare_spec`; edit no serve-only line.
  ]]></action>
  <verify><![CDATA[`test_parser.cscript` through the driver prints `TSO-08 PASS` and the build legs of `TSO-13 PASS`; `test_qualifier_in_stata.cscript` through the driver prints its ALL line and `python3 -m pytest test/test_join_order.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>dash build and dash serve wrote the same operator columns and spec map as the one-line route.</done>
</task>

<task type="auto" id="42-08">
  <name>Take the columns in, saved</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-42.8 (the four constants after `_DASH_QUAL_NAME_RE`; `_dash_tsop_cols_named`, `_dash_take_tsop_columns`, `_dash_tsop_labels` after `_dash_qual_cols_named`, each with a docstring citing E5 and TR-42.4; `_dash_take_qual_columns`' `keep` keyword) and the saved half of TR-42.9 in `DashRenderer._load_data`. Apply TR-42.11's copy-list lines at S42's two anchors. `ServerAppBuilder._glyph_layer_lines` is HIGH: warn in the progress output first.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py -q -n 6 -p no:cacheprovider -k "saved or NamedInTheSpec or TakingTheColumnsIn or TheLabels" ` passes; `python3 -m pytest test/test_join_order.py test/test_qualifier_columns.py test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The saved renderer validated and kept the operator columns, refused every other reserved column, and read twoway's text for them.</done>
</task>

<task type="auto" id="42-09">
  <name>Take the columns in, served</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `ServerAppBuilder._generate_app_source` is HIGH: warn first. Apply the served half of TR-42.9 in the generated data load: `_dash_take_tsop_columns` before the qualifier take-out (:34633), `keep=tuple(_tsop_cols)` passed to it, and `var_labels = _dash_tsop_labels(var_labels, _tsop_cols)` after it. Add no other template line in this task.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py -q -n 6 -p no:cacheprovider` passes except `TestTheHelp`; `python3 -m pytest test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads test/test_served_filter_move.py test/test_mode_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The served app took operator columns in as the saved page does, and both modes drew twoway's values and text before and after a move.</done>
</task>

<task type="auto" id="42-10">
  <name>Map the new functions and programs</name>
  <files>test/function_test_map.py, test/program_coverage_map.py</files>
  <action><![CDATA[
    Add TR-42.13's three `FUNCTIONS` keys under S42's anchor of `test/function_test_map.py` and the two `COVERAGE["dash.ado"]` entries under S42's anchor of `test/program_coverage_map.py`, alphabetically.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>Every new function and program named its test.</done>
</task>

<task type="auto" id="42-11">
  <name>Document operators in the help</name>
  <files>dash.sthlp</files>
  <action><![CDATA[
    Apply TR-42.14: the operator paragraph in "Plot types" after the string-variable sentences (:250 at c96facd; find it by text) and the sp500 example in "Syntax, Description". Edit no other paragraph (R3); every new line is at most 79 characters; name no tool or vendor. If 42-01 found a pinned plot-varlist test (none at `c96facd`, E10), stop and report it before editing: its file is not in this task's `<files>`, and the orchestrator adds a flip task naming it (R9).
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_ts_operators.py::TestTheHelp" "test/test_help_claims_1.py::TestThePlotTypesSection" test/test_help_conformance.py -q -n 6 -p no:cacheprovider` reports 0 failed; `awk 'length > 79' "$WT/dash.sthlp" | grep -c "D.close"` prints 0.]]></verify>
  <done>The help documented operators, the types twoway takes them on, the computation rule and the text rule.</done>
</task>

<task type="auto" id="42-12">
  <name>Run the suite and make commit 1</name>
  <files>none</files>
  <action><![CDATA[
    Run `test_ts_operators.py`, `test_help_claims_1.py`, `test_join_order.py`, `test_mode_parity.py`, `test_file_headers.py`, `test_cscript_hygiene.py`, `test_fixtures_are_committed.py` and `test_tracking_documents.py` with `-n 6`, and `test_parser.cscript` and the S42 block through the driver (TSO-07 and TSO-10 are commit 2's and are not yet written). Then `git -C "$WT" merge --no-edit main` (expect `Already up to date.`) and one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/42-full-1.log"` in the background, read when `exit=` appears, never relaunched (E6 for the known flaky tests). Stage exactly the files in `$S/42-files-1.txt` plus `test/fixtures/ts_operator_truth.json` with `git add -f`; `git diff --cached --name-only` must list nothing else (G6). Write the message to `$S/42-msg-1.txt` in "Notes: commit messages" form, check G7, commit, check G7 again.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/42-full-1.log"` shows 0 failed and `exit=0`; `git -C "$WT" log -1 --format=%s` ends `(WP-30 P1.7)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0; `grep -c '<!-- WP-30 P1.7 -->' "$WT/CHANGELOG.md"` prints 2.]]></verify>
  <done>Commit 1 drew operators in plot varlists in both modes and routes, green, with the entry, key and markers left for commit 2.</done>
</task>

<task type="auto" id="42-13">
  <name>Write the commit-2 failing tests</name>
  <files>test/test_ts_operators.py, test/test_parser.cscript, test/test_wp30_truth.cscript</files>
  <action><![CDATA[
    On the tree commit 1 left, add the commit-2 stubs to `test/test_ts_operators.py` (`TestTheCsv`, `TestTheNotes`, `TestTheTsColumnNamesNeverReachTheUser`, `TestTheRefusals`), naming `dr._dash_col_display`. Append TSO-07 and TSO-10 to the end of S42's run in `test_parser.cscript`. Leave the truth block unchanged except a comment line naming TSO-07's script. Run the new pytest classes with `-rf` into `$S/42-new-2.log` and `test_parser.cscript` through the driver. Write `$S/42-P1.7-2-failure.txt`: the commit-1 sha, one line per failing node and `TSO-07 FAIL`/`TSO-10 FAIL` with the twoway lines they quote. Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED "$S/42-new-2.log"` is at least 6; `grep -cE "TSO-(07|10) FAIL" "$S/run_test_parser.log"` prints 2; `grep -cE "TSO-0[1-6] PASS" "$S/run_test_parser.log"` prints 6.]]></verify>
  <done>Commit 2's regression tests existed and were shown failing on the tree commit 1 left, with commit 1's cases still passing.</done>
</task>

<task type="auto" id="42-14">
  <name>Refuse by() and bare sort</name>
  <files>dash.ado</files>
  <action><![CDATA[
    Apply TR-42.15 (`r(hasts)` from `_dash_process_segment`, gathered in `_dash_plot` beside `_byq_vv_<k>`; "not sorted" then the one dash hint line, exit 5, before anything is registered) and TR-42.16 (the two twoway lines and exit 198 on E4's 18 types when the bare `sort` meets an operated x). Both programs are UNKNOWN to the index: record their callers by grep in `$S/42-impact.txt` first. Every echo goes through `_dash_say`.
  ]]></action>
  <verify><![CDATA[`test_parser.cscript` through the driver prints `TSO-07 PASS`, and every P1A and LB case still prints PASS.]]></verify>
  <done>dash refused by() with an operated plot variable and a bare sort with an operated x exactly where and as twoway does.</done>
</task>

<task type="auto" id="42-15">
  <name>Head the CSV column by its expression</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    `_dash_csv_meta` is CRITICAL: warn in the progress output first. Apply TR-42.17: the `display_names` keyword and the `headers` key (absent keyword gives today's result exactly); `DashRenderer._csv_button`'s call; the generated `_send_csv` call (:36200, a template line, R12: S42 is the batch's template editor); `_DASH_CSV_JS`'s header line with the `hasOwnProperty` guard. Change no other line of `_DASH_CSV_JS`.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py -q -n 6 -p no:cacheprovider -k TestTheCsv` passes; `python3 -m pytest test/test_export.py test/test_display_format_sites.py test/test_join_order.py test/test_qualifier_columns.py test/test_filter_widget_parity.py -q -n 6 -p no:cacheprovider` reports 0 failed (every file naming `_dash_csv_meta` at c96facd, plus the filter parity file).]]></verify>
  <done>Both modes' CSV downloads headed an operator column by its expression, and every other download was byte for byte unchanged.</done>
</task>

<task type="auto" id="42-16">
  <name>Name operator columns in notes</name>
  <files>dash_render.py</files>
  <action><![CDATA[
    Apply TR-42.18: `_dash_col_display` after `_dash_tsop_labels` and appended to the functions tuple after S42's names; `_dash_load_columns`' `display_names` keyword used at its two format notes; the saved `_load_data` call and the generated call passing the expression map. Then grep every `_dash_display(` site and every `f"dash:` note for a plot-column argument (`grep -n '_dash_display(\|f"dash:' dash_render.py`), route any other reachable one through `_dash_col_display`, and list each site in `$S/42-note-sites.txt` for the commit body.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest test/test_ts_operators.py -q -n 6 -p no:cacheprovider -k "TestTheNotes or NeverReachTheUser"` passes; `python3 -m pytest test/test_statistical_helpers.py::TestTheServedAppCarriesEveryName test/test_resource_limits.py::TestTheServedAppDefinesEveryNameItReads -q -n0 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>No note, page or document named a __dasht column; each named its expression.</done>
</task>

<task type="auto" id="42-17">
  <name>Document refusals and map the helper</name>
  <files>dash.sthlp, test/function_test_map.py</files>
  <action><![CDATA[
    Apply TR-42.19: the operator paragraph gains the `by()` and bare-`sort` refusals in twoway's words and the CSV header rule; `'_dash_col_display'` under S42's anchor of `test/function_test_map.py`, alphabetically. Lines at most 79 characters; no tool or vendor name.
  ]]></action>
  <verify><![CDATA[`python3 -m pytest "test/test_ts_operators.py::TestTheHelp" test/test_function_test_map.py "test/test_help_claims_1.py::TestThePlotTypesSection" -q -n 6 -p no:cacheprovider` reports 0 failed.]]></verify>
  <done>The help documented twoway's two operator refusals and the CSV header, and the helper was mapped.</done>
</task>

<task type="auto" id="42-18">
  <name>Close the entry and make commit 2</name>
  <files>BUGS.md, CHANGELOG.md, test/test_tracking_documents.py</files>
  <action><![CDATA[
    Read the title as `WP30_OPEN["P1.7"]`. Close that BUGS.md entry in place (`- [x]`) with "Notes: BUGS.md Resolution", today's date as `ddmonyyyy`. Delete the `"P1.7"` key line of `WP30_OPEN`. Replace both `<!-- WP-30 P1.7 -->` markers in place with "Notes: CHANGELOG lines" (the New line under `### New`, the refusals under `### Changed behaviour`), the old values taken from both failure files. Run `test_tracking_documents.py`, `test_ts_operators.py`, `test_help_claims_1.py`, `test_cscript_hygiene.py` and `test_fixtures_are_committed.py` with `-n 6`, `test_parser.cscript` and the S42 block through the driver; `git -C "$WT" merge --no-edit main` (expect `Already up to date.`); one full run `"<scratch>/full_suite_queue.sh" "$WT" "$S/42-full-2.log"` in the background, read when `exit=` appears. Stage exactly `$S/42-files-2.txt` plus these three; G6, G7 before and after; commit.
  ]]></action>
  <verify><![CDATA[`tail -3 "$S/42-full-2.log"` shows 0 failed and `exit=0`; `grep -c '<!-- WP-30 P1.7 -->' "$WT/CHANGELOG.md"` prints 0; `grep -c '^    "P1.7": "' "$WT/test/test_tracking_documents.py"` prints 0; `git -C "$WT" log -2 --format=%s` shows both subjects ending `(WP-30 P1.7)`; `git -C "$WT" log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Entry P1.7 was closed naming existing tests, its two markers carried the measured old and new behaviour, and two green commits on wp30-s42 were ready for the merger.</done>
</task>

## Section completion criteria

- Operators are drawn on the 29 types twoway takes them on, in both modes, on the one-line route, `dash build` and `dash serve`, before and after saved and served filter moves, with twoway's values, storage types, formats, value labels and text (fixture probes; TSO-01..TSO-04, TSO-13, TSO-20..TSO-24).
- Every refusal of BR-42.5 and BR-42.7 is twoway's (TSO-05..TSO-07, TSO-10, TSO-11).
- No user-visible surface shows `__dasht`; the CSV header is the expression.
- `_dash_parse_varpart_ts`, `_dash_tsop_gen`, the four Mata functions and the four renderer helpers exist, are mapped, and the module helpers travel to the served app.
- The fixture is generated by its extractor, stamped, committed with `-f` and read by tests.
- Two green commits `(WP-30 P1.7)` exist on `wp30-s42`; the second closes the entry, deletes its key and replaces both markers.

## Notes

- **The interim between the two landings.** After commit 1 lands and before commit 2 does, `by()` with an operated variable draws and a bare `sort` with an operated x is accepted. That state exists only on `wp30-p1` between two consecutive landings of one batch.
- **Storage type is `tsrevar`'s, not double** (E3): `gen double` would shift float-based series by up to 0.000845 in total against twoway's serset.
- **sortpreserve.** `_dash_tsop_gen` must not be `sortpreserve` itself: `tsrevar` needs the user's tsset sort, which `_dash_qual_gen_by` and `_dash_sort_gen` restore (critic c1). If the data are not sorted by the time variable, `tsrevar` says `not sorted` as twoway does.
- **python_exec hazard.** Concurrent Stata sessions can drop `python_exec` from `~/.stata19/console/stata19.rc`; the extractor and the truth block then fail or SKIP. Check the file after each slot run; a SKIP is not a pass.
- **Merge rules for the shared files.**
  - R1: TSO-01..TSO-14 as one run at the end of `test_parser.cscript`; S42's truth block and helpers in their own places.
  - R2: S42's two anchors; the map entries under S42's anchors.
  - R3: "Syntax, Description" and "Plot types" (S42's rows).
  - R4/R5: both `P1.7` markers, the entry and its key, by commit 2 only.
  - R6: `version 19` in every new program; S42's own export-block paragraphs in `_dash_render_immediate` and `_dash_prepare_spec`, separate from S12's, S22's and S34's; the four Mata functions after `_dash_sort_export` with their header-index entries and `_needed` names.
  - R7: one new extractor and fixture.
  - R8: `test_mode_parity.py` is not edited; parity for ts frames lives in `test_ts_operators.py`.
  - R12: S42 is batch 15's one `_generate_app_source` editor (the data load in commit 1, `_send_csv` and the load call in commit 2).
- **Landing (merger).** `gitnexus detect-changes --scope all --repo dash` must name, for commit 1, `_dash_tsop_cols_named`, `_dash_take_tsop_columns`, `_dash_tsop_labels`, `_dash_take_qual_columns`, `DashRenderer._load_data`, `ServerAppBuilder._generate_app_source`, `_glyph_layer_lines` and the constants; for commit 2, `_dash_csv_meta`, `DashRenderer._csv_button`, `_dash_col_display`, `_dash_load_columns`, `_generate_app_source` and `_DASH_CSV_JS`; plus test symbols. dash.ado and Mata symbols are not indexed.
- **Commit messages.** Subjects as in "Commit boundary". Body, in order: the failure file; the measured defect (Overview's block); what changed and where (TR-42.1-TR-42.14 / TR-42.15-TR-42.19, both modes); then one line each: `Regression: test/test_ts_operators.py::<Class>::<test> -- failed at <base sha> with <text>` per node (cscripts as `test/test_parser.cscript TSO-01`, `test/test_wp30_truth.cscript TSO-20`); any `Flipped:` line; `Fixture: test/fixtures/ts_operator_truth.json (scripts/extract_ts_operator_truth.do)`; the note sites of `$S/42-note-sites.txt` (commit 2); commit 2 only `BUGS.md: "Time-series operators in plot varlists, such as line D.close date and lfit y L.x, are refused r(101)" (closed)`.
- **BUGS.md Resolution** (one line, in place):

  ```
  - Resolution: Fixed <ddmonyyyy> (WP-30, P1.7). Time-series operators (L., F., D., S., their combinations, L(1/2).x) are accepted in plot varlists on the 29 types twoway takes them on (dash.ado _dash_parse_varpart_3v, _4v and the new _dash_parse_varpart_ts with varlist(numeric ts); fpfit, fpfitci, lowess, lpoly, lpolyci, histogram and kdensity still refuse them in twoway's words), rewritten by Mata (_dash_tsop_rewrite, _dash_tsop_export, _dash_tsop_meta) into __dasht columns that _dash_tsop_gen computes with tsrevar at build under tsset, in tsrevar's storage type with the base's format and value label, on the one-line route, dash build and dash serve; both modes take them in (_dash_tsop_cols_named, _dash_take_tsop_columns, _dash_take_qual_columns' keep) and read twoway's text for titles, keys and tooltips (_dash_tsop_labels), and filter moves select rows of the computed series. No tsset r(111), string r(109), factor r(101), by() with an operated variable r(5) and a bare sort with an operated x r(198) are refused in twoway's words; the CSV header and notes show the expression (_dash_csv_meta display_names, _dash_col_display). Pinned by test/test_ts_operators.py::TestTheLabelsAreTwowaysText::test_case, ::TestBothModesDrawTheSameValues::test_case, ::TestAFilterMoveKeepsTheComputedSeries::test_saved, ::TestTheCsv::test_the_header_is_the_expression, test/test_parser.cscript TSO-01..TSO-14, test/test_wp30_truth.cscript TSO-20..TSO-24; fixture test/fixtures/ts_operator_truth.json. Residual, deferred (WP-30): [aw=L.x] (P2.14); operators in option variables (mlabel(), colorvar(), by()), where twoway's codes differ from dash's r(198).
  ```
- **CHANGELOG lines** (each replaces its marker in place):

  ```
  ### New
  - Time-series operators in plot varlists are drawn, as twoway draws them: `dash line D.close date`, `dash tsline D.close`, `dash lfit close L.close` and `dash scatter L(1/2).close t` were refused r(101) and now draw in both modes on scatter, line, connected, area, bar, spike, dropline, dot, the lfit/qfit/mspline/mband fits, the range and paired types, tsline and tsrline; each series is computed by Stata at build under tsset, titles and keys read "Closing price, D", and the CSV column is headed D.close. (WP-30, P1.7)

  ### Changed behaviour (may need your do-files changed)
  - Operated plot variables are refused where twoway refuses them, in its words (all r(101) "factor-variable and time-series operators not allowed" before): no tsset ("time variable not set", r(111)); a string variable ("make:  may not use time-series operators on string variables", r(109)); a factor variable ("factor-variable operators not allowed", r(101)); by() with an operated variable ("not sorted", r(5)); a bare sort with an operated x on scatter, line and the other connecting types ("option sort() incorrectly specified", r(198)). (WP-30, P1.7)
  ```
- **Notes for the closeout (S58; A145).**
  - **GAPS2.md G4** (:1378, :1417-1422): `- **Tracked:** Closed in WP-30, BUGS.md "<P1.7 title>", commits <sha1>, <sha2>.` Its plan's claim that the fpfit family takes `ts` is wrong (E2): record it.
  - **DROPIN-REMAINING.md:97** (P1.7): "Closed by <sha1>, <sha2> (WP-30 S42)."
  - **P2.14** (DROPIN): `[aw=L.x]` keeps its row and is told to reuse `_dash_tsop_gen`'s lifecycle (register P1.7.3).
  - **P2.28:** a temporary-frame move must run `_dash_tsop_gen` in the user's frame first (critic gap 5).
  - **New P2 row:** option variables with operators (`mlabel(L.make)` twoway r(111), `colorvar(L.mpg)`/`by(L.foreign)` r(101); dash r(198) for all).
  - **AGENTS.md invariant:** "an operator expression reaches Stata only after `_dash_tsop_rewrite`'s and `_dash_tsop_gen`'s canonical-form checks, and the renderer reads __dasht columns only through `_dash_tsop_cols_named`."
  - **Unverified:** Stata 14-18.5 (M2); Windows and Linux (M4).
