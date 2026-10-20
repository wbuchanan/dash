# Section 05: Value bounds twoway accepts

> Part of: WP-31 · GAPS3 rows: C10a (range(varname), range(# .), bwidth(0), lowess bwidth above 1 -> .8, n(1), per-type level bounds) · Risk: green · Batch: 2 · Depends on: 04 · Blocks: -- · Tasks: 3, 1 commit · Case-id prefix: U05

## Overview

**What is wrong today.** GAPS3 C10 (GAPS3.md:129): "Values twoway accepts are refused: `range(varname)` and `range(# .)`, `degree()` above 3 ..., `n(1)`, `bwidth(0)`, lowess `bwidth()` above 1 (twoway uses .8), ..., `level()` bounds applied to every CI type (and `level(5)` drawn on lfitci where twoway bounds 10-99.99), ...". Evidence dash.ado:2995-3003 (the rule tokens), :3150-3158 (dash's own-bound sentences), :3484-3487. The manifest splits C10 three ways (A1): this section, C10a, takes the parts that are a rules-table edit plus one new value kind; S06 takes the parts needing new parsing (degree 4-7, mlabel elements, scatteri 2/2, yaxis(1 2)); S09 takes axes 3-9.

Measured at `6370ca4` (test_option_validation.cscript's own pins): OV-54 `lowess bwidth(5)` r(198) naming bwidth(); OV-55 `lowess bwidth(0)` r(198); OV-58 `lpoly bwidth(0)` r(198); OV-67 `kdensity n(1)` r(198); OV-86 `function range(10)` r(198); `abbrev_truth.json` records `range` as `dash accepts: False` for `scatter ..., ra(...)` (the varname form is the probe there). `level=num,0,100,x` is untyped, so `lfitci level(5)` is rc 0 and drawn; twoway's `lfitci_parse` passes `level()` to `predict`/`invttail` and refuses outside 10-99.99 (the lpolyci token `level=num,10,99.99@lpolyci` is WP-29 P0.9's measured form of the same rule).

**What twoway accepts** (research/stata-ground-truth.md §1.3): lfit family `Range(numlist min=2 max=2 missingok)` -- `range(. 4000)`, `range(1000 .)` take the data's own bound for the dot; `n(integer 3)` with no lower bound stated (n(1) draws one point); kdensity `RAnge(string asis) N(integer 300) Width(real 0) BWidth(real 0)` -- `bwidth(0)` is the default rule; `range()` takes two numbers or a variable name (`twoway_kdensity.sthlp`: "range(# #) ... range(varname)"); function `RAnge N(integer 300)` -- `range(varname)` takes the variable's min and max; lowess `BWidth(real .8)` any real -- the GAPS3 claim "above 1 twoway uses .8" is lowess's own reset and is MEASURED here (D-05.b); lfitci/qfitci/fpfitci/lpolyci `Level()` bounded 10-99.99 by Stata's level machinery (measured text in WP-29 P0.9: "level() must be between 10 and 99.99 inclusive").

**After this section** each rule is twoway's: `range` is a new value kind `range` (two numbers, `.` allowed where twoway's numlist is missingok, or one numeric variable name resolved to its min and max over the plot's sample); `n` allows 1; kdensity `bwidth(0)` means the default rule; lowess `bwidth()` takes any value twoway takes, and values twoway resets to .8 are reset to .8 in the renderer; `level` is bounded 10-99.99 on the four CI types only (S04's applies table already refuses it elsewhere) with twoway's line. Every change is pinned against twoway in the fixture and the area cscript.

**Test order and commit rule.** 05-01 extractor + red tests, no commit; 05-02 the rule and kind edits, the renderer's range/n/bwidth readers, flips; 05-03 certifies, documents, closes C10a, commits `(WP-31 C10a)`.

### Section decisions (binding on the executor)

- **D-05.a `range(varname)` is resolved in dash.ado, once, over the plot's sample.** The new kind writes `"range":"<min> <max>"` to the spec (so both renderers and the saved JS read numbers as today) and `"range_var":"<name>"` beside it for the hover note; the bounds are `summarize <var> if <plot's if> in <in>` with the graph qualifier (`$dash__gq_if`/`$dash__gq_in`, the WP-27 sample rule for weights) at parse time. After a filter move the range stays the full-sample one; documented (M17): twoway draws once, dash's refit keeps twoway's x range. **Decision for maintainer ratification.**
- **D-05.b lowess bwidth's reset is measured, not assumed.** The extractor compares the serset of `lowess mpg weight, bwidth(1)`, `(1.5)`, `(5)`, `(0)`, `(-1)` with `bwidth(.8)`'s and with `bwidth(.3)`'s; a value whose serset equals `.8`'s is "reset"; one that errors is "refused" with its line. The rule token and `_stata_lowess`'s clamp follow the fixture: expected (GAPS3) `bwidth >= 1 -> .8`; `bwidth <= 0` per measurement.
- **D-05.c `n(1)` draws one point.** `_fit_grid` with `n == 1` returns the range's lower bound alone (`np.linspace(lo, hi, 1)` is `[lo]`); a one-point Line draws nothing visible, as twoway's one-point line does (measured by the extractor's SVG: path count).
- **D-05.d `level` is one typed token.** `level=num,0,100,x` becomes `level=num,10,99.99@lfitci|qfitci|fpfitci|lpolyci` (replacing the lpolyci-only token too); the untyped token is deleted because S04's applies table refuses `level()` on every other type first. The message is twoway's measured line.
- **D-05.e The dash-own sentences go.** In `_dash_validate_value` the `extra` branches for `n` ("dash evaluates up to 10000 points") and lowess `bwidth` ("is the fraction of the sample") are deleted where the bound is now twoway's; `n`'s upper bound 10000 stays dash's resource limit (GAPS3 §5 "deferred by decision") with its sentence.

## Risk: [green] -- rule tokens and one value kind; the renderer reads what the kind writes

**Risk factors.** 1. The contract text in test_option_validation.py (`CONTRACT_PLOT_RULES`, :75-90; 41 tokens) pins the tokens. 2. `range(varname)` needs the sample: the resolver runs inside `_dash_process_segment` where the qualifier is known. 3. S06 edits the same `local plot` lines (dash.ado:2998 holds both `degree=` and `bwidth=`), the same `extra` chain, help lines and contract: S06 is cut after S05 lands (A32). 4. `_fit_grid` (:20969) is copied into the app; the kdensity grid (`_kde_curve`) and function evaluation read `range` separately.

**Mitigation.** 1. The contract is edited in 05-02 with the token count moved and a comment. 2. A new program `_dash_fold_range` after `_dash_fold_bw` (:5578) with the qualifier globals. 3. S05 edits against `6370ca4` without regard to S06 and lands first; S06's worktree is cut from `s3-bugs` after S05's merge (A32, TR-05.1). 4. One helper `_dash_range_bounds(options, x)` (module-level, copy list) used by `_fit_grid`, the kdensity grid and function's range reader.

## Dependencies

- **Depends on: 04** (the applies table: `level`, `range`, `n`, `bwidth` are refused on types that do not take them before this section's value rules run, so the relaxed bounds apply only where the option applies).
- **Blocks: --.**
- **Parallel batch: 2**: S05 lands first, then S06 is cut (A32: the two edit the same lines); S07 runs in parallel with S05. Can run with S07 (weights/operators/hover/dates parsers): it edits none of the `range`, `n`, `bwidth`, `level` tokens, `_fit_grid`, `_stata_lowess`, `_kde_curve` or `_dash_fold_bw`'s neighbourhood. S06 (degree, mlabel, scatteri, yaxis: `_dash_imm_number`, `_dash_mlabel_list`, `_dash_add_glyph`) starts after S05 has landed.

## Evidence

Anchors at `6370ca4`.

### The tokens

dash.ado:2997-3003 (quoted in S04's Evidence): `level=num,0,100,x`, `bwidth=pos,1@lowess  bwidth=pos`, `n=int,1,300@mspline  n=int,2,10000`, `range=numlist,2,2`, `level=num,10,99.99@lpolyci`. The kinds in `_dash_validate_value` (:3098-3620): `num` :3166, `int` :3195, `pos` :3218, `numlist` :3331-3356 (runs Stata's `numlist` on the value; a `.` fails numlist -> refused; a varname fails -> refused). The own-bound sentences :3147-3163:

```stata
3157    else if "`opt'" == "n" & "`ptype'" != "mspline" {
3159        local extra ". dash evaluates up to 10000 points."
3161    else if "`opt'" == "bwidth" & "`ptype'" == "lowess" {
3162        local extra ". lowess bwidth() is the fraction of the sample."
```

The error form (:3615-3618) `"dash: <opt>() must be <bad> (got: <value>)<extra>"`, r(198).

### The renderer's readers

`_fit_grid(x, options, layer="fit")` (dash_render.py:20969; `_FIT_GRID` :474, n default 100) reads `options["range"]` as two floats and `options["n"]`; `GlyphMapper._stata_lowess(x, y, bw=0.8, mean, noweight)` (:16801); `_stata_kde_bandwidth`/`_kde_curve` (:21850/:21911) read kdensity's `bwidth` (0 is not expected: the rule refused it) and `range`; function's range reader in `map_function` (grep `options.get("range"` near :21007 `_fp_grid`? no: `map_function`, grep `def map_function`). All are on the copy list or class members.

### Fixtures on disk

`test/fixtures/value_truth.json` (WP-22 alwidth bounds); `test/fixtures/abbrev_truth.json` `options.range` (dash rejects `ra(...)` on scatter -- S04 now refuses range on scatter for the type, so that record's `dash.accepts: False` keeps its meaning; the varname probe moves to lfit here).

### Existing tests that pin today's behaviour (flip)

| Node / case | Today | After |
|---|---|---|
| test_option_validation.cscript OV-54 `lowess bwidth(5)` (:661) | 198 | per fixture: rc 0 (reset to .8) |
| OV-55 `lowess bwidth(0)` (:662) | 198 | per fixture |
| OV-58 `lpoly bwidth(0)` (:665) | 198 | per fixture (lpoly's `BWidth(string)`: measured) |
| OV-67 `kdensity n(1)` (:674) | 198 | 0 |
| OV-86 `function range(10)` (:693), OV-88 `range(abc)` (:695) | 198 naming range() | OV-86 per fixture (one number: twoway's rc); OV-88 r(111) `variable abc not found` if twoway says so |
| test_option_validation.py `CONTRACT_PLOT_RULES` (:75-90), `assert len(want) == 41` (:233) | tokens as quoted | `level=num,10,99.99@lfitci\|qfitci\|fpfitci\|lpolyci`, `bwidth=num@lowess  bwidth=num,0@kdensity  bwidth=pos`, `n=int,1,300@mspline  n=int,1,10000`, `range=range,2,2,m@lfit\|qfit\|lfitci\|qfitci  range=range,2,2`; count 41 -> 42 with `# 41 -> 42: C10a range typed, level typed, bwidth kdensity` (41 is the value at S05's base, re-read at 05-02; recount after writing; A33) |
| test_option_validation.py:496-497 (`"level() must be a number between 0 and 100" not in body`) | -- | unchanged (guard) |
| test_help_claims_1.py HC1-16 (:495) `yaxis(3), degree(4), bin(2000)` | -- | S06/S09's; not S05's |
| dash.sthlp "Option values" :941-1002 sentences on n(), bwidth(), level(), range() | dash's bounds | twoway's (TR-05.8) |
| test_unsupported_report_is_true.py LIVE_VALUES `"bwidth": ({"bwidth":"300"},{"bwidth":"700"},"lpoly")` | -- | unchanged |

## User stories

- **US-05.1** As a twoway user, I want `lfit mpg weight, range(. 4000)` and `kdensity mpg, range(weight)` to draw, so my do-file runs unchanged.
- **US-05.2** As a twoway user, I want `lowess mpg weight, bwidth(5)` to draw what twoway draws (its .8 curve) rather than stop.
- **US-05.3** As a twoway user, I want `lfitci mpg weight, level(5)` refused with twoway's line, not drawn.
- **US-05.4** As a twoway user, I want `kdensity mpg, bwidth(0)` and `lfit ..., n(1)` accepted as twoway accepts them.

## Business requirements

- **BR-05.1** `range(# .)`, `range(. #)` on lfit qfit lfitci qfitci take the data's bound for `.`; `range(varname)` on lfit-family, kdensity and function takes the variable's min and max over the plot's sample; a variable not found is r(111) with twoway's line; `range(#)` (one number) returns twoway's rc and line.
- **BR-05.2** `n(1)` is accepted where `n()` applies; the layer draws one point.
- **BR-05.3** kdensity `bwidth(0)` draws the default-bandwidth curve (identical to no `bwidth()`).
- **BR-05.4** lowess `bwidth(#)` for every # the fixture marks "reset" draws the `.8` curve; "refused" values are refused with twoway's rc and line.
- **BR-05.5** `level()` outside 10-99.99 on lfitci qfitci fpfitci lpolyci is r(198) with twoway's line; 10 and 99.99 are accepted.
- **BR-05.6** Both renderers agree on every accepted value (parity).

## Technical requirements

- **TR-05.1 Rule tokens** in `_dash_option_rules` `local plot` (:2997-3003). **Sequencing (DECISIONS A32):** S05 and S06 edit the same lines (dash.ado:2998 holds `degree=int,0,3  bwidth=pos,1@lowess  bwidth=pos` -- S05 edits bwidth, S06 degree; the `extra` chain :3147-3163; dash.sthlp :944 and :996; test_option_validation.py `CONTRACT_PLOT_RULES` :75-90 and the `len(want)` line :233). S05 lands on `s3-bugs` FIRST within batch 2 and S06's worktree is cut after S05's merge (both stay in batch 2; S07 runs in parallel with S05). S05 therefore edits against `6370ca4` without regard to S06, and S06 reads S05's landed tokens. The tokens:
  - `level=num,0,100,x` -> deleted; `level=num,10,99.99@lpolyci` -> `level=num,10,99.99@lfitci|qfitci|fpfitci|lpolyci`.
  - `bwidth=pos,1@lowess  bwidth=pos` -> `bwidth=num@lowess  bwidth=num,0@kdensity  bwidth=pos` (lowess: any number, the renderer resets per fixture; kdensity: 0 or more; lpoly/lpolyci keep `pos` unless the fixture's `lpoly_bwidth_0` is rc 0, then `bwidth=num,0@lpoly|lpolyci` too).
  - `n=int,2,10000` -> `n=int,1,10000`.
  - `range=numlist,2,2` -> `range=range,2,2,m@lfit|qfit|lfitci|qfitci  range=range,2,2` (`m` = missingok).
- **TR-05.2 Kind `range`** in `_dash_validate_value` after the `numlist` branch (:3356): `p1,p2` counts, `p3 == "m"` missingok. Value trimmed: (a) one token that is a Stata name (`regexm(T, "^[A-Za-z_][A-Za-z0-9_]*$")`): first `capture confirm variable <tok>`; rc 111 -> `display as error "variable `tok' not found"`, `exit 111` (twoway's line, measured `range.var_missing`); then `capture confirm numeric variable <tok>`; rc 7 (`'<tok>' found where numeric variable expected` -- `confirm numeric variable` returns r(7), never r(109); REVIEW-1 R1-17) -> print the fixture's `range.var_string` line with its rc; else `norm` = `"@var:<fullname>"` (resolved by `_dash_fold_range`, TR-05.3); (b) else `numlist` with `missingok` when `p3 == "m"`: `capture numlist "<value>", missingok` (no double quote in the value, as the numlist kind guards), count in `p1..p2`, `norm` = the expanded list with `.` kept; a count outside -> `bad` = twoway's line for one number (fixture `range.one_number.message`, expected "range() invalid -- invalid numlist" r(121)? the fixture decides the rc: the kind exits with the fixture's rc when the fixture's `rc != 198`).
- **TR-05.3 `_dash_fold_range ptype`** (new sclass program after `_dash_fold_mlabv` :2118ff; called in `_dash_process_segment` after `_dash_validate_opts` (:5584) and before `_dash_stylelist_check` (:5585)): if `s(range)` starts `@var:`, `quietly summarize <name> $dash__gq_if $dash__gq_in` (the plot's own `if`/`in` as `_dash_seg_weight_s` applies them -- read :5579-5582 for the locals), `sreturn local range "`r(min)' `r(max)'"` (`%21.0g`), `sreturn local range_var "<name>"`; an all-missing variable -> `range` empty and a note `dash: range(<name>): no observations, the data's own range used`. JSON key list: add `range_var` after `range`. `_dash_require_mata`: no Mata added. program_coverage_map.py: `"_dash_fold_range": ("test_option_validation.cscript:U05-01",)`.
- **TR-05.4 `_dash_range_bounds(options, x)`** (new module-level function after `_fit_grid` :20969ff): returns `(lo, hi)` floats from `options.get("range")` tokens, a `.`/missing token replaced by `np.nanmin(x)`/`np.nanmax(x)`; no range -> the data's; never raises. `_fit_grid` uses it (replacing its own two-float read); the kdensity grid reader (`_kde_curve`'s caller in `map_kdensity`, grep `"range"` in :18200-18420) and `map_function`'s range reader use it. Copy list: `"_dash_range_bounds",` after `"_fit_grid",` (functions tuple :46822-47270; `test_statistical_helpers.py::TestTheServedAppCarriesEveryName`).
- **TR-05.5 `n(1)`.** `_fit_grid`: `n = max(1, int(...))`; `np.linspace(lo, hi, n)`; nothing else divides by `n - 1` (grep `n - 1` in :20969-21010).
- **TR-05.6 kdensity `bwidth(0)`.** In `map_kdensity`'s bandwidth read (grep `_stata_kde_bandwidth` call in :18200-18420): a parsed `bwidth` of 0 is treated as absent (the rule-of-thumb path); the saved JS twin (`_FILTER_JS` kdensity branch `bw_fixed`) receives `bw_fixed: None` through the config, so no JS edit (verify `ac.bw_fixed` handling at :25285-25375 treats null as the rule).
- **TR-05.7 lowess reset.** `GlyphMapper._stata_lowess` (:16801): at entry `if bw >= 1.0: bw = 0.8` (and `bw <= 0` per the fixture's `lowess_bwidth.reset` list); the served copy follows (class member). The S16 JS twin (batch 5) must copy the clamp: Notes.
- **TR-05.8 Messages.** `_dash_validate_value`: delete the `n` and lowess `bwidth` `extra` branches (:3157-3163) except n's 10000 sentence ("dash evaluates up to 10000 points." stays for `n > 10000`); for `opt == "level"` the `bad` text is replaced by twoway's measured line printed verbatim: after `local bad` is set, `if "`opt'" == "level" & "`bad'" != "" { display as error "<fixture level.message>"; exit 198 }` where the literal is copied from the fixture (expected `level() must be between 10 and 99.99 inclusive`).
- **TR-05.9 Help (R3).** dash.sthlp "Option values" (:941-1002): the sentences on `bwidth()` ("a fraction of the sample, so at most 1" :943), `n()` ("2 to" :996), `level()` and `range()` are rewritten to twoway's bounds; the "Five say so in a second sentence" sentence (:994-998) loses n() and lowess bwidth(). "Differences from twoway": one sentence on `range(varname)` resolved once over the sample (D-05.a). S06 edits the `degree()` and `yaxis()` words of the same paragraph: S05 touches only the sentences naming its four options.
- **TR-05.10 Security.** The variable name reaches `confirm`/`summarize` as a Stata name matched by regex (letters, digits, underscore) -- never a macro or expression; the min/max are numbers; `range_var` reaches JSON through the same escaper as every key.

## Boundaries

- Not S05's: `degree`, `yaxis`/`xaxis`, `mlabel`, scatteri (S06); axes 3-9 (S09); `bin` (resource limit, kept); the applies table (S04); `_dash_fold_bw`'s kdensity `width()` synonym (unchanged); `_FILTER_JS` (S10 is batch 3's editor; the kdensity `bw_fixed: None` path exists); the lowess JS twin (S16); the appliers; help paragraphs beyond TR-05.9.

## Stata truth

**New extractor** `scripts/extract_value_bounds_truth.do` (head form of scripts/extract_default_base_truth.do, `ZV_` globals, twoway only), run as `DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s05 $WT/scripts/extract_value_bounds_truth.do`, writing `test/fixtures/value_bounds_truth.json` (`git add -f`). `sysuse auto`; each probe `capture noisily twoway ... nodraw` (or drawn and `serset` read where the curve matters), rc and the first error line recorded; sersets compared with `serset use` / `mata: st_data()` sums:

| Key | Command | Recorded |
|---|---|---|
| `range.dot_hi`, `range.dot_lo` | `lfit mpg weight, range(. 4000)` / `range(1000 .)` | rc; serset x min/max |
| `range.var_lfit`, `range.var_kdensity`, `range.var_function` | `lfit mpg weight, range(weight)`; `kdensity mpg, range(weight)`; `function y=x, range(weight)` | rc; serset x min/max (expect `summarize weight` min/max) |
| `range.var_missing`, `range.var_string` | `lfit mpg weight, range(nosuch)` / `range(make)` | rc, message |
| `range.one_number`, `range.three` | `lfit mpg weight, range(10)` / `range(1 2 3)`; `function y=x, range(10)` | rc, message |
| `n.one`, `n.zero` | `lfit mpg weight, n(1)` / `n(0)`; `kdensity mpg, n(1)` | rc, message; SVG path count for n(1) |
| `bwidth.kdensity_0` | `kdensity mpg, bwidth(0)` | rc; serset equals `kdensity mpg`'s |
| `bwidth.lpoly_0` | `lpoly mpg weight, bwidth(0)` | rc, message |
| `lowess_bwidth.<v>` for v in `1 1.5 5 0 -1 .3 .8` | `lowess mpg weight, bwidth(v)` | rc, message; serset y sum; `reset` = 1 when equal to `.8`'s and not to `.3`'s |
| `level.<v>` for v in `5 9.99 10 99.99 100 50` on lfitci; `level.qfitci_5`, `level.fpfitci_5`, `level.lpolyci_5` | `<type> mpg weight, level(v)` | rc, message |

**Truth block** `* ==== S05 C10a: Value bounds ====` in `test/test_wp31_truth.cscript`:
- **U05-01** `dash lfit mpg weight, range(weight)`: the spec's `range` equals `summarize weight` min/max; the saved and served fit x min/max equal twoway's serset min/max (fixture); `range(. 4000)` and `range(1000 .)` likewise.
- **U05-02** `dash kdensity mpg, bwidth(0)`: the curve equals `dash kdensity mpg`'s (both modes); `dash lowess mpg weight, bwidth(5)`: the curve equals `bwidth(.8)`'s and differs from `bwidth(.3)`'s (both modes), for each fixture value marked `reset`.
- **U05-03** `dash lfit mpg weight, n(1)`: rc 0; the fit source has one row (both modes).

**Area cases** (test_option_validation.cscript, after the last case, header lines): **U05-04** `level(5)`, `level(9.99)`, `level(100)` on lfitci, `level(5)` on qfitci, fpfitci, lpolyci: dash rc 198 and line equal twoway's (same run); `level(10)`, `level(99.99)` rc 0. **U05-05** `range(nosuch)`, `range(make)`, `range(10)`, `range(1 2 3)` on lfit; `function y=x, range(10)`: rc and line equal twoway's. **U05-06** every `lowess_bwidth.<v>` with `rc != 0` in the fixture: dash's rc and line equal twoway's. OV-54, OV-55, OV-58, OV-67, OV-86, OV-88 flipped in place to the fixture's rc (their `_ov_case` third argument), each with a comment `// Flipped (WP-31 C10a): twoway's rc`.

## TDD test stubs

### Regression tests, `test/test_value_bounds.py` (new; red at `6370ca4` unless guard)

- Test: fixture stamped; `lowess_bwidth.5.reset == 1`; `level.5.rc == 198` -- `TestTheFixture::test_meta_is_stamped`, `::test_twoways_readings` (guard after 05-01).
- Test: the rule block holds the TR-05.1 tokens and no `level=num,0,100,x` -- `TestTheTokens::test_level_is_typed`, `::test_range_is_the_range_kind`, `::test_n_allows_one`, `::test_bwidth_allows_zero_on_kdensity` (red).
- Test: `_dash_range_bounds` for `"1 10"`, `". 10"`, `"1 ."`, none, with NaNs in x -- `TestRangeBounds::test_each_form` (red: no function); it is on the copy list -- `::test_served_copy` (red).
- Test: `_fit_grid` with `n == 1` returns one point at `lo`; with `range ". 4000"` the grid's max is 4000 and min the data's -- `TestFitGrid::test_one_point`, `::test_dot_bound` (red).
- Test: `_stata_lowess(bw=5)` equals `bw=0.8` and differs from `0.3` (fixture `reset` list drives the parametrization) -- `TestLowessReset::test_reset_values[v]` (red).
- Test: `map_kdensity` with `bwidth "0"` equals no bwidth (curve arrays) and the agg config's `bw_fixed` is None -- `TestKdensityZero::test_zero_is_the_rule` (red if the mapper reads 0 as fixed).
- Test: a spec with `range_var` renders in both modes and the hover/notes name nothing new -- `TestRangeVar::test_both_modes[mode]` (guard).
- Test: `_dash_validate_value`'s source holds no "fraction of the sample" sentence and no untyped n sentence for n<=10000 -- `TestMessages::test_dash_own_sentences_removed` (red).

### Cases in cscripts

- `test_wp31_truth.cscript` U05-01..U05-03 (red); `test_option_validation.cscript` U05-04..U05-06 (red), OV flips.

### Flips

- test_option_validation.py contract text and count (`# 41 -> N: C10a ...`); OV-54/55/58/67/86/88 in place; any pytest node 05-01's grep finds using `lowess bwidth(>=1)` expecting refusal or `lfitci level(<10)` expecting a drawing (grep `level": "5\|bwidth": "5\|level(5)` in test/*.py).

### Parity corpus (R8; guards)

`test/test_mode_parity.py` under `# WP-31 C10a`: `CORPUS` "lfit range(. 4000)", "kdensity range(weight)", "lowess bwidth(5)", "kdensity bwidth(0)", "lfit n(1)".

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| range forms | pytest `TestRangeBounds`, `TestFitGrid`; U05-01, U05-05 | `range.*` | yes |
| n(1) | pytest `TestFitGrid::test_one_point`; U05-03 | `n.*` | yes |
| kdensity bwidth(0) | pytest `TestKdensityZero`; U05-02 | `bwidth.kdensity_0` | yes |
| lowess reset | pytest `TestLowessReset`; U05-02, U05-06 | `lowess_bwidth.*` | yes |
| level bounds | U05-04 | `level.*` | n/a |
| Contract | test_option_validation.py | -- | n/a |

**Acceptance criteria**
- **AC-05.1** Every fixture probe with rc 0 is rc 0 in dash and draws twoway's range/curve (U05-01..U05-03); every probe with rc != 0 is refused with the same rc and line (U05-04..U05-06).
- **AC-05.2** `python3 -m pytest test/test_value_bounds.py test/test_option_validation.py test/test_statistical_helpers.py test/test_lowess*.py test/test_kdensity*.py test/test_mode_parity.py -k "C10a or lowess or kdensity or lfit" -q -p no:cacheprovider` 0 failed.
- **AC-05.3** test_option_validation.cscript prints U05-04..U05-06 PASS, the flipped OV cases PASS, `ALL CHECKS PASSED`, no SKIP; the truth script U05-01..U05-03 PASS.

## Tasks

**Commit boundary.** 05-01 to 05-03 are the one C10a commit, subject `Accept the range(), n(), bwidth() and level() values twoway accepts, with its bounds (WP-31 C10a)`, on `wp31-s05` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s05`. Body: `<scratch>/05-01-failure.txt`, the measured defect (OV-54/55/67/86 refusals; `lfitci level(5)` drawn), what changed where (both renderers), `Regression:` lines, `Flipped: test/test_option_validation.cscript OV-54 -- r(198) was wrong because twoway draws lowess bwidth(5) as .8 (C10a)` and the others, `Fixture: test/fixtures/value_bounds_truth.json (scripts/extract_value_bounds_truth.do)`, `BUGS.md: "<S01's C10a title>" (closed)`, `GAPS3: C10a Tracked`.

<task type="auto" id="05-01">
  <name>Measure the bounds and write failing tests</name>
  <files>scripts/extract_value_bounds_truth.do, test/fixtures/value_bounds_truth.json, test/test_value_bounds.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp31-s05` and the base holds S04's `BEGIN applies` (`grep -c "BEGIN applies" dash.ado` is 1); `mkdir -p <scratch>/s05`. Create scripts/extract_value_bounds_truth.do by the "Stata truth" table (head from scripts/extract_default_base_truth.do lines 1-60 with ZV_ globals; serset comparisons through `serset use` after each drawn graph, `mata: st_numscalar(...)` sums; `_meta`; `sort_keys=True`); run through the slot; `git add -f test/fixtures/value_bounds_truth.json`. Write the `reset` list and the rc of `bwidth.lpoly_0` and `n.one` to `<scratch>/s05/readings.txt`. Create test/test_value_bounds.py with the classes of "TDD test stubs" (parametrized from the fixture where it says so). Grep for pins: `grep -ln 'level": "5\|bwidth": "5\|range(weight)\|n": "1"' test/*.py` and the six OV cases; list in `<scratch>/s05/05-flips.txt`. Run `python3 -m pytest test/test_value_bounds.py -q -n0 -p no:cacheprovider -rf > <scratch>/s05/05-01.log 2>&1`; write `<scratch>/05-01-failure.txt`. Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/value_bounds_truth.json'));print(sorted(d['_meta']), d['level']['5']['rc'], d['lowess_bwidth']['5']['reset'])"` prints the five meta keys, `198` and `1` (a different reading stops the task for a second look at the probe); `grep -c FAILED <scratch>/s05/05-01.log` is at least 8; `test -s <scratch>/05-01-failure.txt`.]]></verify>
  <done>twoway's acceptance, resets and refusals of the range, n, bwidth and level values were recorded in a stamped fixture, and the regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="05-02">
  <name>Relax the rules and read the values</name>
  <files>dash.ado, dash_render.py, test/test_option_validation.py</files>
  <action><![CDATA[
    Make TR-05.1 (the four token lines, following `<scratch>/s05/readings.txt` for lpoly bwidth(0) and the lowess reset list), TR-05.2 (kind `range` after the numlist branch), TR-05.3 (`_dash_fold_range` after `_dash_fold_mlabv`, its call after `_dash_validate_opts` at :5584, `range_var` in the JSON key list, the program_coverage_map.py entry), TR-05.8 (messages: level's literal from `fixture['level']['5']['message']`). In dash_render.py make TR-05.4 (`_dash_range_bounds` after `_fit_grid`, used by `_fit_grid`, the kdensity range reader and map_function's; copy-list entry after `"_fit_grid",`), TR-05.5, TR-05.6, TR-05.7 (the clamp in `_stata_lowess` from the reset list). Edit test_option_validation.py `CONTRACT_PLOT_RULES` to the new tokens and the `len(want)` assertion with `# 41 -> <N>: C10a level typed on the ci types, range typed with missingok, kdensity bwidth 0`. Add function_test_map.py `'_dash_range_bounds': 'test/test_value_bounds.py::TestRangeBounds::test_each_form'`. Run `python3 -m pytest test/test_value_bounds.py test/test_option_validation.py test/test_statistical_helpers.py test/test_function_test_map.py test/test_program_coverage_map.py -q -n0 -p no:cacheprovider` and the files in `<scratch>/s05/05-flips.txt` (flip their pytest nodes in place with `Flipped:` lines appended to the file).
  ]]></action>
  <verify><![CDATA[`grep -c "level=num,0,100,x" dash.ado` prints 0; `grep -c "range=range" dash.ado` prints 2; `grep -c '"_dash_range_bounds",' dash_render.py` prints 1; `grep -c "fraction of the sample" dash.ado` prints 0; the pytest run reports 0 failed.]]></verify>
  <done>The rules took twoway's bounds, range() read a dot or a variable, n(1) drew one point, kdensity bwidth(0) took the rule, lowess reset its bandwidth as twoway does, and level() was bounded on the four CI types with twoway's line.</done>
</task>

<task type="auto" id="05-03">
  <name>Certify, document, close C10a and commit</name>
  <files>test/test_wp31_truth.cscript, test/test_option_validation.cscript, dash.sthlp</files>
  <action><![CDATA[
    Append the block `* ==== S05 C10a: Value bounds ====` holding U05-01..U05-03 above the marker line of test/test_wp31_truth.cscript, in the form S01's Notes give (S01 writes no stub, D-01.e; helpers above the header; one row, one block, A14), and U05-04..U05-06 in test_option_validation.cscript (after the last case, before `// Summary`, header lines), and flip OV-54, OV-55, OV-58, OV-67, OV-86, OV-88 in place to the fixture's rc with the `// Flipped (WP-31 C10a)` comment and their header lines (:84-88, :118-120) rewritten. Append the parity CORPUS cases under `# WP-31 C10a`. Run both cscripts through the driver (`WP31_ONLY=S05`) and `python3 -m pytest test/test_mode_parity.py -q -n0 -p no:cacheprovider -k "C10a"`. Make TR-05.9 in dash.sthlp. TWOWAY_COVERAGE_AUDIT.md rows 87, 90, 99, 100: append ` [WP-31 C10a: corrected -- range(varname) and range(# .) read, n(1), kdensity bwidth(0), lowess bwidth reset, level() bounded 10-99.99]`. Close S01's "C10a" BUGS.md entry in BRIEF's form (functions _dash_option_rules, _dash_validate_value kind range, _dash_fold_range, _dash_range_bounds, _fit_grid, GlyphMapper._stata_lowess; both renderers; pinned by test/test_value_bounds.py::TestTheTokens::test_level_is_typed, test/test_wp31_truth.cscript U05-01, test/test_option_validation.cscript U05-04; fixture test/fixtures/value_bounds_truth.json; Residual, deferred (WP-31): range(varname) is resolved once over the sample and does not follow a filter move (D-05.a)); GAPS3 §9 C10a -> `Closed in WP-31, BUGS.md "<S01's C10a title>", commit pending.` (A11: the merger's step k.3b writes the landed sha; no amend). CHANGELOG: replace `<!-- WP-31 C10a -->` under `### Results that change` with `- lfit, qfit, lfitci and qfitci accept range(. #) and range(# .) (refused before); lfit-family, kdensity and function accept range(varname), the variable's min and max over the plot's sample; n(1) is accepted (n() needed 2); kdensity bwidth(0) is the default rule (refused before); lowess bwidth() values twoway resets to .8 draw the .8 curve (bwidth(5) was refused). (WP-31, C10a)`; under `### Changed behaviour` with `- level() outside 10 to 99.99 on lfitci, qfitci, fpfitci and lpolyci is refused, r(198), with twoway's line level() must be between 10 and 99.99 inclusive; dash drew lfitci level(5). (WP-31, C10a)`; under `### Fixed in WP-31` with `- Value bounds of range(), n(), bwidth() and level() are twoway's. (WP-31, C10a)`. Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py test/test_help_claims_1.py -q -n0 -p no:cacheprovider`. Stage the C10a files (`git add -f` the fixture), check names, write `<scratch>/s05/msg.txt`, grep for `claude|anthropic` (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c "U05-0[1-3] PASS" <scratch>/s05/run_test_wp31_truth.log` prints 3; `grep -c "U05-0[4-6] PASS" <scratch>/s05/run_test_option_validation.log` prints 3 and the log ends `ALL CHECKS PASSED`; `grep -c SKIP` on both prints 0; `git log -1 --format=%s` ends `(WP-31 C10a)`; `grep -c "(WP-31, C10a)" CHANGELOG.md` prints 3; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Stata certified the relaxed and tightened bounds against twoway's own, the help described twoway's bounds, C10a was closed in BUGS.md and GAPS3, and one green commit on wp31-s05 was ready for the merger.</done>
</task>

## Section completion criteria

- The four rule lines read as TR-05.1; kind `range` exists; `_dash_fold_range` resolves a variable; `_dash_range_bounds` on the copy list; `n(1)` draws one point; kdensity `bwidth(0)` is the rule; lowess resets per fixture; `level` bounded on four types with twoway's line.
- U05-01..U05-06 PASS; six OV cases flipped; contract updated; parity cases green; one commit `(WP-31 C10a)`; BUGS and GAPS3 closed; three CHANGELOG lines.

## Notes

- **Order in `_dash_process_segment`.** `_dash_fold_range` runs AFTER `_dash_validate_opts` (which wrote `@var:<name>`) and BEFORE `_dash_stylelist_check`; the spec writer reads `s(range)` later, so it sees numbers.
- **The applies table first.** With S04 landed, `level(5)` on scatter is refused for the type before this section's bound; U05-04 therefore probes CI types only.
- **For S16 (lowess JS, batch 5).** `dash_lowess` must clamp `bw` exactly as `_stata_lowess` does (TR-05.7) or the saved refit diverges from the served one.
- **For S10 (JS prelude, batch 3).** `dash_fit_grid` must accept `n == 1` and a `.` bound: read `_dash_range_bounds` and port it.
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after each cscript run.
- **Shared files (R1-R13).** R1: the S05 block and three area cases plus six flips in test_option_validation.cscript. R2: one functions-tuple entry after `"_fit_grid",`. R3: the four options' sentences in "Option values" and one "Differences" sentence. R4: three C10a markers. R5: one entry. R6: `_dash_fold_range` added after `_dash_fold_mlabv`; `version 19`. R7: new fixture. R8: five CORPUS cases. R9: flips recorded. R10: the contract count with its comment. R12: S05 is batch 2's first `_dash_option_rules` editor (S06 is cut after S05 lands; the same token lines, A32).
- **Decision for maintainer ratification.** D-05.a (range(varname) resolved once over the sample at parse time; does not follow a filter move).
