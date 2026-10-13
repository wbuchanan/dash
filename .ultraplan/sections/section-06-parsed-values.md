# Section 06: Values that need new parsing

> Part of: WP-31 · GAPS3 rows: C10b (degree 4-7 with the ROT constants, several variables in one mlabel() element, scatteri 2/2, yaxis(1 2)), C18, F4 · Risk: yellow · Batch: 2 · Depends on: 04, 05 (cut after S05 lands, A32) · Blocks: 09 · Tasks: 5, 3 commits · Case-id prefix: U06

## Overview

**What is wrong today.** GAPS3 C10 (GAPS3.md:129) lists among the values twoway accepts and dash refuses: "`degree()` above 3 (ROT constants for 4-7 exist but are unreachable)", "one `mlabel()` element naming several variables", "scatteri `2/2`", "`yaxis(1 2)`". C18 (GAPS3.md:137): "Immediate forms: `scatteri` `2/2` numlist refused where twoway divides", evidence dash_parse.mata (the immediate-values reader, `_dash_imm_number` at :2186-2216 on this tree; GAPS3 cites :1166 from an older tree). F4 (GAPS3.md:211): "`_LPOLY_ROT_CONSTANTS` holds degree 4-7 rows that are unreachable under `degree=int,0,3`", dash_render.py:486. The manifest gives this section C10b (A1); S05 has the rules-table-only bounds, S09 axes 3-9.

Measured at `6370ca4`: test_option_validation.cscript OV-51 `lpoly degree(5)` r(198) "dash fits local polynomials up to degree 3"; test_parser.cscript P1A-61 refuses `scatteri 2/2 1` r(198) ("2/2 is a numlist range twoway takes and then evaluates as a division, drawing 1", :728-731); `_dash_mlabel_list` (dash.ado:3713-3770) validates each unquoted element as one variable (`_dash_validate_value ... "var"`), so `mlabel(t*)` is r(111); `yaxis=int,1,2` refuses `yaxis(1 2)` as not an integer; HC1-16 (test_help_claims_1.py:495) and dash.sthlp:930-931 show `yaxis(3)` and `degree(4)` refused.

**What twoway does.** lpoly `DEGree(integer 0)` with no upper bound (`lpoly_parse:34-47`); dash's `_default_lpoly_bwidth` already carries Stata's rule-of-thumb constants for `pe` = 5 and 7 (degree 4-7), dormant (dash_render.py:483-486, test_lpoly_rot.py's degree 4/5 tier at 5e-4). `MLabels(string)` is unabbreviated and expanded with `unab` so `t*` is `trunk turn`, one label variable per y in order. scatteri reads each coordinate with `gettoken` and a numlist-like `confirm`: `2/2` reaches an evaluation as a division and draws 1 (`dash_parse.mata:1887-1893` comment, measured 23sep2026; `1/2` is refused by twoway too; `0/0` missing; `(1/1)` a clock position). `yaxis(numlist)`: twoway's graph class strips `yaxis()` and places the plot on EVERY axis named, drawing the series twice when two are given (`twowaygraph_g.class` ParseOpts :612-651; measured here by the extractor: the number of plots in `.Graph.plotregion1` and the axes they are on).

**After this section** `degree(4..7)` fits with the dormant constants reached (above 7 stays dash's bound, measured against twoway's acceptance and documented); an `mlabel()` element is `unab`'d and its names fill successive y slots; `scatteri 2/2 1` draws at (1, 1); `yaxis(1 2)` draws the layer on both axes, two renderers (one per range), in both modes; the stale `_LPOLY_ROT_CONSTANTS` comment says the rows are live. Three commits: `(WP-31 C10b)`, `(WP-31 C18)`, `(WP-31 F4)` -- F4's is the constants comment and its test, made with C10b's degree change in the same task sequence but as its own commit per row.

**Test order and commit rule.** One regression test file per row (A14): C10b has three (`test_yaxis_both.py`, `test_lpoly_degree.py`, `test_mlabel_patterns.py`), C18 one (`test_scatteri_division.py`), F4 one (`test_lpoly_constants_live.py`). 06-01 extractor, fixture and the yaxis tests, no commit; 06-02 the degree, mlabel and scatteri test files, no commit; 06-03 degree + yaxis + mlabel (C10b) with flips, commit; 06-04 scatteri division (C18), commit; 06-05 F4's test file (written red against the tree 06-04 leaves), comment and closeout, commit. No commit stages a later row's red case.

### Section decisions (binding on the executor)

- **D-06.a `yaxis(1 2)` draws the layer twice.** `_dash_add_glyph` calls the mapper once per axis token with an options copy whose `yaxis` is that token; `_dash_assign_axis_ranges` (dash_render.py:33568ff) then puts the second copy on `y2`. Legend: one key (twoway's, measured `.legend` key count); the second copy's renderers get `legend_label` suppressed by the existing `colorvar_key=False`-style mechanism or by removing the duplicate `LegendItem` after both draw (whichever the mapper exposes; the test pins one key). The hull sees both ranges' renderers through `y_range_name`. Bound stays 1..2 here; S09 raises it to 9 (same token form).
- **D-06.b The new kind is `axes`.** `yaxis=axes,1,2  xaxis=axes,1,2`: a numlist of distinct integers each in `[p1, p2]`, 1 to 2 elements, normalised to `"1"`, `"2"` or `"1 2"` (sorted). The renderer reads `str(options.get("yaxis","1")).split()`; every `== "2"` test of the yaxis string (`_dash_add_secondary_axes` :31764-31768, `_dash_assign_axis_ranges` :33578-33582, `_compute_secondary_range`, `_dash_axis_vars` :1288, `_dash_layer_axis_names` :1252, the JS `_DASH_AXIS_FINISH_JS` readers if any) becomes `"2" in tokens`. dash.ado's `_seg_yaxis_out` (:5749-5753) becomes the max token for the WP-29 P0.5 axis check and a new `_seg_yaxes_out` carries the list.
- **D-06.c `mlabel(t*)` expands in place.** In `_dash_mlabel_list`, an unquoted element that is not `.`, `..`, `...`, `=` is passed through `capture unab names : <element>`; rc 111 keeps today's path (`_dash_validate_value ... "var"` refuses with twoway's line); rc 0 with k names replaces the element by k elements before the per-y loop. Names beyond `nser` are dropped as twoway drops extra label variables (measured: `scatter mpg weight, mlabel(t*)` rc and labels); `mlabel(make-foreign)` ranges likewise.
- **D-06.d scatteri `p/q`.** In `_dash_imm_number`, before `_dash_imm_numchars`: when the token holds exactly one `/` with decimal numbers on both sides (`_dash_imm_decimal` each), and `strtoreal(p) == strtoreal(q)`: `0/0` -> `"null"`, else `"1"` (the division); `p != q` -> `""` (twoway's "invalid point", as P1A-61 says for `1/2`). `(1/1)` stays a clock position (read before the number, unchanged). The hexadecimal `1.0X+3ff` stays refused (documented, P1A-61).
- **D-06.e degree above 7.** The constants stop at `pe = 7`. `degree=int,0,7` with the own-bound sentence "dash fits local polynomials up to degree 7" for 8+; twoway's behaviour at degree(8) is recorded in the fixture and documented under M17.

## Risk: [yellow] -- the axis routing is read in many places; two renderers per layer touch the hull, legend and moves

**Risk factors.** 1. `yaxis == "2"` string tests are scattered (grep `"yaxis"` gives 14 sites in dash_render.py); one missed site draws the second copy on the wrong range. 2. Two renderers per layer: the saved filter script copies rows per source (one source, two renderers: fine), the served redraw draws the layer again (`_dash_redraw_for` calls `_dash_draw_layer` -> `_dash_add_glyph`: both copies rebuilt). 3. Legend duplicates. 4. `unab` on user text: the element must be a Stata name pattern, never an expression. 5. Batch partners: S05 edits `local plot` lines `range= n= bwidth= level=`; S06 edits `degree=` and `yaxis=/xaxis=` (:2995, :2998 -- :2998 also holds S05's `bwidth=` tokens, the `extra` chain :3147-3163, dash.sthlp :944/:996 and the contract are shared too, so S06 is cut after S05 lands, A32, and every anchor is re-read on that tree); S07 edits the parsers for weights/operators/hover/dates -- not `_dash_mlabel_list`.

**Mitigation.** 1. `test_yaxis_both.py::TestEverySiteReadsTokens` greps the sites listed in TR-06.3 for `.split()`/`in` reads; the both-modes tests draw `yaxis(1 2)` and assert two renderers with `y_range_name` `default` and `y2`. 2. MOVE_CORPUS case. 3. One legend key pinned. 4. `unab` only on text matching `^[A-Za-z_*?~][A-Za-z0-9_*?~-]*$` (Stata name chars and wildcards; `-` for ranges), read by value. 5. S06's worktree is cut from `s3-bugs` after S05 has landed (A32); 06-01 checks `grep -c "bwidth=num@lowess" dash.ado` prints 1 before anything else.

## Dependencies

- **Depends on: 04** (the applies table: `degree` applies to lpoly/lpolyci only, so `degree=int,0,7` never fires elsewhere; `yaxis`/`xaxis` are not in the table).
- **Blocks: 09.** S09 (axes 3-9, batch 3) is written against this section's `axes` kind, `_dash_axis_tokens`, the pair loop in `_dash_add_glyph` and the `_dash_assign_axis_ranges` early return (A32; index row 09 `Depends on: 01, 06`); it raises the kind's bound and the renderer's range names on the tree this section leaves. S10 (JS prelude) ports nothing of this section (lpoly's JS is S19).
- **Parallel batch: 2**, cut after S05 lands (A32: S05 and S06 edit the same lines -- dash.ado:2998, the `extra` chain :3147-3163, dash.sthlp :944/:996, test_option_validation.py's `CONTRACT_PLOT_RULES` and `len(want)` line); runs in parallel with S07 only (disjoint functions, Risk factor 5).

## Evidence

Anchors at `6370ca4`.

### degree

dash.ado:2998 `degree=int,0,3`; :3151-3153 `else if "`opt'" == "degree" { local extra ". dash fits local polynomials up to degree 3." }`. dash_render.py:483-486:

```python
483 # repr(_lpoly_rot_constant(k, p)) for p = 1, 3, 5, 7: that quadrature with the
484 # kernel's support strict (|z| < support).  p = 5, 7 (degree 4-7) are dormant
485 # while degree() is capped at 3 (section 11 SD-7).
486 _LPOLY_ROT_CONSTANTS = {
```

`_default_lpoly_bwidth` (:16922) reads `C = _LPOLY_ROT_CONSTANTS.get((kernel, pe))` at :21753 with `pe` the odd degree at or above the requested one; `GlyphMapper._compute_lpoly_fit` (:16960) takes any `degree`. test_lpoly_rot.py (:19, :407-443) already checks degree 4/5 rows of its fixture at 5e-4 against `_default_lpoly_bwidth` directly.

### mlabel elements

dash.ado `_dash_mlabel_list` (:3713-3770): per element `_c` is `skip|eq|dots|name`; a `name` goes to `_dash_validate_value "`prefix'" "mlabel" "var" ...` (:3747), one variable. `_dash_fold_mlab` (:2045) runs first (histogram/function/mspline/mband). The renderer reads the normalised per-y list (`_dash_mlabel_names`, dash_render.py:36476).

### scatteri

dash_parse.mata `_dash_imm_number` (:2186-2216): `if (!_dash_imm_numchars(t)) return("")` -- `/` is not a number character (`_dash_imm_numchars` :2070-2088: digits, `+-.`, hex letters, `xX`), so `2/2` is "invalid point". The header comment :1887-1893 records twoway's division. test_parser.cscript P1A-61 (:728-744) lists `"scatteri 2/2 1"` among 198 refusals.

### yaxis

dash.ado:2995 `yaxis=int,1,2  xaxis=int,1,2`; :3148-3150 the "dash draws two axes." sentence; :5747-5753 `_seg_yaxis_out` = `real(s(yaxis))` else 1; `_dash_route_axis2` (dash_parse.mata:7015) routes `axis(#)` suboptions, not the layer's `yaxis()`. dash_render.py: `_dash_add_secondary_axes` (:31720) `wanted = any(str(p.get("options", {}).get(axis_key, "1")).strip() == "2" for p in plots)` (:31764-31766); `_dash_assign_axis_ranges` (:33568-33596) `use_y2 = ... == "2"` then `r.y_range_name = "y2"` for the layer's renderers; `_compute_secondary_range` (:11840); `_dash_layer_axis_names` (:1252); `_dash_axis_vars(plots, axis_no=1)` (:1288); `_dash_add_glyph` (:42344-42404) dispatches once per layer.

### Fixtures on disk

`test/fixtures/lpoly_rot_truth.json` (degree 0-5 rows, test_lpoly_rot.py); `test/fixtures/axis2_truth.json` (WP-29 P0.5 second-axis truth); none for mlabel expansion or scatteri division.

### Existing tests that pin today's behaviour (flip)

| Node / case | Today | After |
|---|---|---|
| test_option_validation.cscript OV-51 `lpoly degree(5)` (:658) | 198 | 0 (`// Flipped (WP-31 C10b)`); a new U06-01 pins degree(8) per fixture |
| test_option_validation.cscript OV-32 `scatter yaxis(3)` (:631) | 198 | unchanged (S09 flips it) |
| test_option_validation.py `CONTRACT_PLOT_RULES` `yaxis=int,1,2  xaxis=int,1,2`, `degree=int,0,3` (:80, :83) | -- | `yaxis=axes,1,2  xaxis=axes,1,2`, `degree=int,0,7`; count unchanged (the value on the batch-2 tree after S05 -- 42 -- re-read at 06-03, A33) |
| test_parser.cscript P1A-61 list `"scatteri 2/2 1"` (:737) and comment :728-731 | refused | removed from the list; U06-05 asserts it draws (1, 1); comment rewritten |
| test_help_claims_1.py HC1-16 (:495-499) `degree(4)` "refused" | -- | `degree(4)` removed from the refused set (yaxis(3), bin(2000) stay until S09) |
| test_help_examples.py:125 `'dash (scatter mpg weight, yaxis(3))': 1` | -- | unchanged (S09) |
| dash.sthlp:930-931 example `yaxis(3)` and :944 "degree() 0 to 3", :994-998 | -- | degree sentence -> 0 to 7; yaxis sentence -> "1, 2 or both (1 2)" |
| test_lpoly_rot.py (degree 4/5 tier) | reads the function directly | unchanged (guard); a new mapper-level test draws degree(4) |
| any pytest spec with `"yaxis": "2"` read as equality in a test helper (grep `== "2"` in test/*.py) | -- | unchanged unless it builds `yaxis(1 2)` |

## User stories

- **US-06.1** As a twoway user, I want `lpoly mpg weight, degree(4)` to fit with Stata's rule of thumb for that degree.
- **US-06.2** As a twoway user, I want `scatter mpg price weight, mlabel(t*)` to label each y with the next variable the pattern expands to.
- **US-06.3** As a twoway user, I want `scatteri 2/2 1` to draw where twoway draws it.
- **US-06.4** As a twoway user, I want `line y x, yaxis(1 2)` drawn against both axes as twoway draws it, in both modes, following filter moves.

## Business requirements

- **BR-06.1** `degree(4)`..`degree(7)` on lpoly and lpolyci draw; the default bandwidth equals twoway's `r(bwidth)` for that degree and kernel within test_lpoly_rot.py's 5e-4 tier; `degree(8)` behaves as the fixture records (refused by dash with its own sentence if twoway accepts: documented).
- **BR-06.2** An unquoted `mlabel()` element that `unab` expands to k variables labels the next k y's; a name twoway refuses is refused with its line; nothing else about mlabel changes.
- **BR-06.3** `scatteri p/q x` with `p == q` draws at y = 1 (missing for 0/0); `p != q` is refused as twoway refuses it.
- **BR-06.4** `yaxis(1 2)` (and `xaxis(1 2)`) draws the layer on both axes; the second axis appears; one legend key; both renderers follow a filter move; `yaxis(2 1)`, `yaxis(1 1)` normalise to `1 2` / `1` as twoway reads them (fixture).
- **BR-06.5** Saved and served agree.

## Technical requirements

- **TR-06.1 degree.** (Anchors as at `6370ca4`; re-read on the tree after S05 landed, where :2998 reads `degree=int,0,3  bwidth=num@lowess  bwidth=num,0@kdensity  bwidth=pos` and the `extra` chain has lost S05's branches, A32.) dash.ado:2998 `degree=int,0,3` -> `degree=int,0,7`; :3152 sentence -> `". dash fits local polynomials up to degree 7."`. dash_render.py:483-485 comment -> "p = 5, 7 (degree 4-7) are live since WP-31 C10b/F4; degree() is bounded at 7 because the quadrature table stops there (section 11 SD-7)". `_default_lpoly_bwidth` and `_compute_lpoly_fit` need no change (they take any degree; verify `pe` mapping at :21753 gives 5 for degree 4-5 and 7 for 6-7).
- **TR-06.2 `axes` kind.** `_dash_validate_value`: new branch after `int` (:3217): `bad` = "a list of one or two distinct integers between `p1' and `p2'"; `capture numlist "<T>", integer min(1) max(2) range(>=`p1' <=`p2')` (no quote in the value); distinct (`: list uniq`), `norm` = the sorted list. Tokens :2995 -> `yaxis=axes,1,2  xaxis=axes,1,2`; the extra sentence :3148-3150 stays ("dash draws two axes."). dash.ado :5749-5753: `_seg_ya` = the max token (`word count`/`max` via Mata `max(strtoreal(tokens()))`), unchanged downstream; add `c_local _seg_yaxes_out "`s(yaxis)'"` for a future reader (S09).
- **TR-06.3 Renderer sites** (each `== "2"` becomes a token test; helper `_dash_axis_tokens(options, key) -> list[str]` new module-level function, copy list after `"_dash_reference_lines",` (R2), returning `str((options or {}).get(key, "1")).split() or ["1"]`): `_dash_add_secondary_axes` :31764-31766 (`wanted = any("2" in _dash_axis_tokens(p.get("options"), axis_key) for p in plots)`); `_dash_assign_axis_ranges` :33578-33582 (`use_y2 = "2" in _dash_axis_tokens(options, "yaxis") and "y2" in fig.extra_y_ranges`, same for x); `_compute_secondary_range` :11840ff (its per-plot filter); `_dash_layer_axis_names` :1252; `_dash_axis_vars` :1288; `_dash_hover_layer_vars`/`_dash_layer_tick_format` if they read yaxis (grep). `_DASH_AXIS_FINISH_JS` (:30933): grep `yaxis`; if it compares the string, read tokens in JS (`String(v).split(/\s+/)`) -- S06 is batch 2's one editor of that constant if so (R11 lists S24 as batch 8's; batch 2 has no listed editor; note in hand-back).
- **TR-06.4 Two renderers.** In `_dash_add_glyph` (:42344-42404), before the dispatch: `_yt = _dash_axis_tokens(options, "yaxis"); _xt = _dash_axis_tokens(options, "xaxis")`; when `len(_yt) > 1 or len(_xt) > 1`, loop over the cartesian pairs `(y, x)`, building `_o = dict(options, yaxis=y, xaxis=x)` and calling the existing dispatch path with `_o`, collecting the renderers; after the first pair, pass `legend=False`-equivalent: set `r.glyph`'s renderer `legend_label` off by removing the `LegendItem`s the later pairs added (`fig.legend[0].items` entries whose `renderers` are the later pairs' renderers) so one key remains (D-06.a); the caller (`_make_figure_body` :43981-44023 and the served `_dash_draw_layer` :49137-49225) calls `_dash_assign_axis_ranges(fig, renderers, options)` per layer today: it must be called per pair with `_o` -- do this INSIDE `_dash_add_glyph` for the multi-axis case (import nothing new; `_dash_assign_axis_ranges` is module-level and copied) and leave the callers unchanged, so neither `_make_figure_body` nor `_generate_app_source` is edited (R12: S06 is not their editor; S07 may be). **The callers still call `_dash_assign_axis_ranges(fig, renderers, options)` afterwards with the layer's own options (`yaxis "1 2"`), under which `use_y2 = "2" in tokens` is True and both copies would move to `y2` (REVIEW-1 R1-04): so `_dash_assign_axis_ranges` returns at once when `len(_dash_axis_tokens(options, "yaxis")) > 1 or len(_dash_axis_tokens(options, "xaxis")) > 1` (the pair loop has assigned per copy). `TestBothAxes::test_callers_do_not_reassign[mode]` asserts the two `y_range_name`s after a full `_make_figure_body`/served build.**
- **TR-06.5 mlabel expansion.** `_dash_mlabel_list` (:3713): after `_c` is computed and before the `named`/`seen` handling for `"name"`, insert: if the element matches `^[A-Za-z_*?~][A-Za-z0-9_*?~-]*$` and holds `*`, `?`, `~` or `-`, `capture unab _mlx : <element>`; on rc 0 splice `_mlx`'s names into the element list in place (`_mlt<j>..`, shifting later elements; `_mln` grows) and continue with the first spliced name; on rc != 0 fall through to `_dash_validate_value ... "var"` (twoway's line). A plain name takes today's path. Measured behaviour for more names than y's: dropped silently (fixture `mlabel.extra_names`); for a quoted element: untouched.
- **TR-06.6 scatteri division.** dash_parse.mata `_dash_imm_number` (:2186): after the `.a-.z` check and before `_dash_imm_numchars`, insert:
  ```mata
      // twoway's numlist reads p/q as a range; with one value it is then
      // evaluated as a division: 2/2 and -1/-1 draw at 1, 0/0 is missing
      // (measured 23sep2026; WP-31 C18).  p != q is "invalid point".
      k = strpos(t, "/")
      if (k > 1 & k < strlen(t) & strpos(substr(t, k + 1, .), "/") == 0) {
          a = substr(t, 1, k - 1)
          b = substr(t, k + 1, .)
          if (_dash_imm_decimal(a) & _dash_imm_decimal(b)) {
              if (strtoreal(a) == strtoreal(b)) {
                  return(strtoreal(a) == 0 ? "null" : "1")
              }
              return("")
          }
      }
  ```
  (declare `real scalar k; string scalar a, b`). Header comment :1887-1893: "Two things" -> "One thing" (the hex literal) and note the division is drawn. Header index entry for `_dash_imm_number` gains "p/q with p == q draws 1".
- **TR-06.7 Maps.** function_test_map.py: `'_dash_axis_tokens': 'test/test_yaxis_both.py::TestTokens::test_each_form'`. program_coverage_map.py: `_dash_imm_number` already mapped (test_parser.cscript); add `"test_parser.cscript:U06-05"` to its tuple.
- **TR-06.8 Help (R3).** dash.sthlp "Option values": `degree()` "0 to 3" -> "0 to 7" (:944, :996); `yaxis()`/`xaxis()` "1 or 2" -> "1, 2 or both (yaxis(1 2) draws the layer on both axes)" (:944, :994-995; the `yaxis(3)` example :930-931 is S09's); Marker labels: one sentence "an mlabel() element may be a varlist pattern (t*, make-foreign): its variables label the following y's"; scatteri paragraph: "a coordinate p/q with p equal to q is 1 (0/0 missing), as twoway evaluates it"; Secondary axes (:3826): "a layer on yaxis(1 2) is drawn on both axes". lpoly paragraph (:3112): degree 0-7.
- **TR-06.9 Security.** `unab` sees a regex-checked name pattern only; the division reads two decimal strings through `strtoreal`; the axis tokens are "1"/"2" literals after validation; no new text sink.

## Boundaries

- Not S06's: `range n bwidth level` tokens and `_fit_grid` (S05); axes 3-9, `yaxis(3)` pins, `_dash_add_secondary_axes`'s range creation beyond the token read (S09); `_make_figure_body`, `_generate_app_source`, `_FILTER_JS` (not edited: TR-06.4 keeps the change inside `_dash_add_glyph`); the lpoly JS twin (S19); `_dash_fold_mlab`'s type rules; `mlabvposition`; the hex literal refusal; the appliers; scheme files.

## Stata truth

**New extractor** `scripts/extract_parsed_values_truth.do` (head form of scripts/extract_default_base_truth.do, `ZP_` globals, twoway only), run as `DASH_REPO=$WT $WT/scripts/stata_slot.sh <scratch>/s06 $WT/scripts/extract_parsed_values_truth.do`, writing `test/fixtures/parsed_values_truth.json` (`git add -f`). `sysuse auto`:

| Key | Command | Recorded |
|---|---|---|
| `degree.<d>` for d in 4 5 6 7 8 | `lpoly mpg weight, degree(d) nograph` (the command, not twoway: it returns `r(bwidth)`); then `capture noisily twoway lpoly mpg weight, degree(d)` | `r(bwidth)`, `r(degree)`; twoway's rc and message |
| `degree.kernels` | `lpoly mpg weight, degree(4) kernel(k) nograph` for the eight kernels | `r(bwidth)` each |
| `mlabel.pattern` | `twoway scatter mpg price weight, mlabel(t*)` | rc; `.plotregion1.plot1.style.label` variables / serset label columns (trunk, turn) in order |
| `mlabel.extra_names` | `twoway scatter mpg weight, mlabel(t*)` | rc, message (expected rc 0, second name dropped) |
| `mlabel.range` | `twoway scatter mpg price weight, mlabel(make-foreign)` | rc; label variables |
| `mlabel.bad_pattern` | `twoway scatter mpg weight, mlabel(zz*)` | rc, message (expected r(111) "variable zz* not found") |
| `scatteri.<form>` for `2/2 1`, `-1/-1 1`, `0/0 1`, `1/2 1`, `1 2 (1/1)` | `twoway scatteri <form>` | rc, message; serset y x values; for `(1/1)` the clock position |
| `yaxis.both` | `twoway line mpg weight, yaxis(1 2)` | rc; `.Graph.plotregion1` plot count (expect 2), each plot's `.yaxis` number; `.legend` key count; `.yaxis2` present |
| `yaxis.order`, `yaxis.dupe`, `yaxis.three` | `yaxis(2 1)`, `yaxis(1 1)`, `yaxis(1 2 3)` | rc, message, plot count |
| `xaxis.both` | `twoway line mpg weight, xaxis(1 2)` | the same |

**Truth block** `* ==== S06 C10b: Parsed values ====` appended by 06-03 above the marker line of `test/test_wp31_truth.cscript` (C10b is the section's only measured row: one block, A14; S01 writes no stub, D-01.e; C18's case is in test_parser.cscript and F4 has none):
- **U06-01** `dash lpoly mpg weight, degree(d)` for d 4..7: dash's default bandwidth (`r._dash_agg_config` or the mapper's `_default_lpoly_bwidth` call through the registered spec) equals `degree.<d>.r_bwidth` within 5e-4 relative, both modes; `degree(8)`: dash's rc equals the fixture's reading (or dash's own 198 when twoway accepts, documented, U06-01 then asserts the sentence names 7).
- **U06-02** `dash scatter mpg price weight, mlabel(t*)`: the spec's `mlabel` is `trunk turn`; both modes draw two LabelSets with those columns.
- **U06-03** `dash line mpg weight, yaxis(1 2)`: two Line renderers, `y_range_name` `default` and `y2`, a right axis, one legend key, both modes; after a dropdown move both follow (served `_on_filter_change`; saved node run).
- **U06-04** (area, test_option_validation.cscript) `yaxis(1 1)`, `yaxis(2 1)`, `yaxis(1 2 3)`, `yaxis(0)`: dash rc and line equal twoway's (same run); OV-51 flipped to rc 0.
- **U06-05** (test_parser.cscript, after P1A-61) `scatteri 2/2 1`, `-1/-1 1` draw one point at (1, 1) (the spec's `values`); `0/0 1` is missing (drawn as nothing, rc 0); `1/2 1` stays r(198); `1 2 (1/1)` clock 1 -- each rc equal to twoway's from the same run.

## TDD test stubs

### Regression tests (new; red at `6370ca4` unless guard)

`test/test_lpoly_degree.py` (C10b; written in 06-02):
- Test: fixture stamped; `degree.4.r_bwidth` finite -- `TestTheFixture::test_meta_is_stamped` (guard after 06-01).
- Test: `GM().map_lpoly(...)` with `degree "4".."7"` draws and the bandwidth equals the fixture within 5e-4 for epanechnikov and each kernel -- `TestDegree::test_four_to_seven[d]`, `::test_kernels[k]` (red: the rule is dash.ado's, so here the mapper test is a guard; the RED part is `TestTheRule::test_degree_token_is_0_7` reading dash.ado).
- Test: both modes draw degree(5) alike -- `TestBothModes::test_degree_five[mode]` (guard).

`test/test_yaxis_both.py`:
- Test: `_dash_axis_tokens` for `"1"`, `"2"`, `"1 2"`, missing, `" 2 "` -- `TestTokens::test_each_form` (red: no function); on the copy list -- `::test_served_copy` (red).
- Test: a spec with `yaxis "1 2"` renders two renderers for the layer with `y_range_name` {"default", "y2"}, a right axis, one legend key -- `TestBothAxes::test_two_renderers[mode]`, `::test_one_legend_key[mode]`, `::test_the_second_axis_exists[mode]` (red: today the spec never carries "1 2"; building it by hand, `== "2"` fails and one renderer draws).
- Test: `xaxis "1 2"` likewise -- `::test_xaxis_both[mode]` (red).
- Test: both renderers follow a saved move (node) and a served move -- `TestMoves::test_saved`, `::test_served` (red).
- Test: after a full `_make_figure_body` and a served build the two copies keep `y_range_name` `default` and `y2` (the callers' later `_dash_assign_axis_ranges` call returns at once for a multi-token option, TR-06.4, R1-04) -- `TestBothAxes::test_callers_do_not_reassign[mode]` (red).
- Test: every site in TR-06.3 reads tokens (source grep: no `== "2"` on a yaxis/xaxis read remains in dash_render.py) -- `TestEverySiteReadsTokens::test_no_equality_read_remains` (red).

`test/test_mlabel_patterns.py` (C10b; written in 06-02):
- Test: `_dash_mlabel_list`'s source holds the `unab` splice (reads dash.ado) -- `TestTheSplice::test_unab_is_used` (red); the pattern regex is anchored and allows `* ? ~ -` only -- `::test_the_pattern_is_bounded` (red).
- Test: a spec `mlabel "trunk turn"` on two y's draws two LabelSets (guard: the renderer already reads per-y lists).

`test/test_scatteri_division.py` (C18; written in 06-02, red at the base and against the tree 06-03 leaves):
- Test: the Mata source of `_dash_imm_number` holds the `/` branch (reads dash_parse.mata) -- `TestDivision::test_the_branch_exists` (red); the header comment names one refused accident, the hex literal -- `::test_the_comment` (red).
- Test: `map_scatteri` from a spec whose values hold y 1 (as dash.ado will write for 2/2) draws at (1, 1) -- guard.

`test/test_lpoly_constants_live.py` (F4; its own file, A14; written in 06-05 against the tree 06-04 leaves, red there):
- Test: the comment at dash_render.py:483-485 says the degree 4-7 rows are live, not dormant -- `TestTheComment::test_constants_are_live` (red).
- Test: for each `(kernel, pe)` key of `_LPOLY_ROT_CONSTANTS`, `_default_lpoly_bwidth` with `degree = pe - 1` on a small frame reads that key (monkeypatch the dict with a sentinel per key; each read once) -- `TestTheComment::test_every_row_is_reachable` (red until the comment test's sibling exists; it is the proof F4 asks for).

### Cases in cscripts

- `test_wp31_truth.cscript` U06-01..U06-03 (red); `test_option_validation.cscript` U06-04 (red), OV-51 flip; `test_parser.cscript` U06-05 (red) with the P1A-61 list edit.

### Flips

- OV-51; test_option_validation.py contract tokens (`yaxis=axes,1,2  xaxis=axes,1,2`, `degree=int,0,7`; count unchanged, comment `# C10b: axes kind, degree 7`); P1A-61 list and comment (:728-737); HC1-16's `degree(4)` (test_help_claims_1.py:495-499 and the help text it reads, dash.sthlp:930-931 keeps yaxis(3)); test_lpoly_rot.py: none.

### Parity corpus (R8; guards)

`test/test_mode_parity.py` under `# WP-31 C10b/C18`: `CORPUS` "lpoly degree(5)", "scatter mpg price weight mlabel(t*)" (the frame has `trunk`? use the parity frame's own columns: `mlabel(p*)` -> price, pricemiss), "line yaxis(1 2)", "scatteri 2/2 1"; `MOVE_CORPUS` "line yaxis(1 2), dropdown to Foreign" (`_MOVES[0]`).

## Test plan

| What | How | Fixture | Both modes? |
|---|---|---|---|
| degree 4-7 bandwidth | pytest `TestDegree`; U06-01 | `degree.*` | yes |
| mlabel pattern | pytest `TestTheSplice`; U06-02 | `mlabel.*` | yes |
| yaxis(1 2) two renderers, legend, axis, moves | pytest `TestBothAxes`, `TestMoves`; U06-03; MOVE_CORPUS | `yaxis.*` | yes |
| yaxis list refusals | U06-04 | `yaxis.order/dupe/three` | n/a |
| scatteri p/q | U06-05; pytest `TestDivision` | `scatteri.*` | yes (CORPUS) |
| F4 comment | pytest `TestTheComment` | -- | n/a |

**Acceptance criteria**
- **AC-06.1** `degree(4..7)` draws with the fixture's bandwidth within 5e-4 in both modes; the rule and sentence say 7.
- **AC-06.2** `mlabel(t*)` labels successive y's as twoway's serset shows; `mlabel(zz*)` is refused with twoway's line.
- **AC-06.3** `yaxis(1 2)` and `xaxis(1 2)` draw two renderers per layer on the two ranges, one legend key, both modes, through moves; `yaxis(1 1)`, `(2 1)`, `(1 2 3)`, `(0)` match twoway's rc and line.
- **AC-06.4** `scatteri 2/2 1` draws (1, 1); `1/2 1` refused; `0/0` missing.
- **AC-06.5** U06-01..U06-05 PASS, no SKIP; `python3 -m pytest test/test_lpoly_degree.py test/test_yaxis_both.py test/test_mlabel_patterns.py test/test_scatteri_division.py test/test_lpoly_constants_live.py test/test_option_validation.py test/test_lpoly_rot.py test/test_axis2_suboptions.py test/test_immediate_values.py test/test_help_claims_1.py test/test_mode_parity.py -k "C10b or C18 or yaxis or lpoly or scatteri" -q -p no:cacheprovider` 0 failed.

## Tasks

**Commit boundary.** 06-01 to 06-03 form the C10b commit, subject `Accept degree(4-7), mlabel() varlist elements and yaxis(1 2), as twoway does (WP-31 C10b)`; 06-04 the C18 commit, subject `Evaluate a scatteri coordinate p/p as twoway does (WP-31 C18)`; 06-05 the F4 commit, subject `Mark the degree 4-7 rule-of-thumb constants live (WP-31 F4)`; all on `wp31-s06` in `$WT=/Users/billy/Desktop/Programs/StataPrograms/d/dash-wt/wp31-s06`, cut from `s3-bugs` after S05 landed (A32). Bodies in BRIEF's forms: the saved failure text (`<scratch>/06-01-failure.txt` for C10b, `<scratch>/06-04-failure.txt` for C18, `<scratch>/06-05-failure.txt` for F4), the measured defect, what changed where (both renderers), `Regression:`, `Flipped:` (OV-51; P1A-61 `"scatteri 2/2 1"`; HC1-16 degree(4); the contract), `Fixture: test/fixtures/parsed_values_truth.json (scripts/extract_parsed_values_truth.do)`, `BUGS.md: "<title>" (closed)`, `GAPS3: <row> Tracked`. Every GAPS3 Tracked line a closing task writes ends `commit pending.` (A11: the merger's step k.3b writes the landed sha in one tracking commit per batch; no `git commit --amend` anywhere).

<task type="auto" id="06-01">
  <name>Measure twoway and write the yaxis tests</name>
  <files>scripts/extract_parsed_values_truth.do, test/fixtures/parsed_values_truth.json, test/test_yaxis_both.py</files>
  <action><![CDATA[
    Check `git -C $WT branch --show-current` prints `wp31-s06`, `grep -c "BEGIN applies" dash.ado` prints 1 (S04 landed) and `grep -c "bwidth=num@lowess" dash.ado` prints 1 (S05 landed: this worktree is cut after S05, A32; a 0 stops the task); `mkdir -p <scratch>/s06`. Create scripts/extract_parsed_values_truth.do by the "Stata truth" table (head from scripts/extract_default_base_truth.do lines 1-60 with ZP_ globals; `lpoly ..., nograph` for `r(bwidth)`; `.Graph` class reads for plot counts and axes; sersets for scatteri values and mlabel columns; `_meta`; `sort_keys=True`); run through the slot; `git add -f test/fixtures/parsed_values_truth.json`. Record `yaxis.both.plots` (expect 2) and `degree.8.rc` in `<scratch>/s06/readings.txt`; a plot count other than 2 stops the task for a second look. Create test/test_yaxis_both.py with its classes of "TDD test stubs" (TestTokens, TestBothAxes including test_callers_do_not_reassign, TestMoves, TestEverySiteReadsTokens). Run `python3 -m pytest test/test_yaxis_both.py -q -n0 -p no:cacheprovider -rf > <scratch>/s06/06-01.log 2>&1` and write `<scratch>/06-01-failure.txt` (base sha, the failing nodes with reasons, guards passed; 06-02 appends the degree and mlabel nodes). Do not commit.
  ]]></action>
  <verify><![CDATA[`python3 -c "import json;d=json.load(open('test/fixtures/parsed_values_truth.json'));print(sorted(d['_meta']), d['yaxis']['both']['plots'], d['scatteri']['2/2 1']['rc'])"` prints the five meta keys, `2` and `0`; `grep -c FAILED <scratch>/s06/06-01.log` is at least 6; `test -s <scratch>/06-01-failure.txt`; `git -C $WT status --porcelain` shows no staged file.]]></verify>
  <done>twoway's degree bandwidths, mlabel expansion, scatteri division and two-axis drawing were recorded in a stamped fixture, and the two-axis regression tests were shown failing on the unmodified tree.</done>
</task>

<task type="auto" id="06-02">
  <name>Write the degree, mlabel and scatteri tests</name>
  <files>test/test_lpoly_degree.py, test/test_mlabel_patterns.py, test/test_scatteri_division.py</files>
  <action><![CDATA[
    Create test/test_lpoly_degree.py (TestTheFixture, TestDegree, TestBothModes, TestTheRule; no F4 class -- F4's tests are test/test_lpoly_constants_live.py, written in 06-05, A14), test/test_mlabel_patterns.py (TestTheSplice and the two-LabelSet guard) and test/test_scatteri_division.py (TestDivision and the map_scatteri guard) with the classes of "TDD test stubs". Grep pins: `grep -n 'degree(4)\|degree(5)\|2/2\|yaxis(1 2)' test/*.py test/*.cscript` -> `<scratch>/s06/06-flips.txt`, each line marked C10b or C18. Run `python3 -m pytest test/test_lpoly_degree.py test/test_mlabel_patterns.py -q -n0 -p no:cacheprovider -rf > <scratch>/s06/06-02.log 2>&1` and append the failing nodes with reasons to `<scratch>/06-01-failure.txt` (C10b's text); run `python3 -m pytest test/test_scatteri_division.py -q -n0 -p no:cacheprovider -rf > <scratch>/s06/06-02-c18.log 2>&1` and write `<scratch>/06-04-failure.txt` (C18's text; refreshed in 06-04). Do not commit.
  ]]></action>
  <verify><![CDATA[`grep -c FAILED <scratch>/s06/06-02.log` is at least 2 (test_degree_token_is_0_7, test_unab_is_used, test_the_pattern_is_bounded); `grep -c FAILED <scratch>/s06/06-02-c18.log` is at least 2; `test -s <scratch>/06-04-failure.txt`; `grep -c "C10b\|C18" <scratch>/s06/06-flips.txt` equals its line count; `git -C $WT status --porcelain` shows no staged file.]]></verify>
  <done>The degree, mlabel and scatteri regression tests existed in their own files, one per row, and were shown failing for their recorded reasons, and nothing was committed.</done>
</task>

<task type="auto" id="06-03">
  <name>Draw degree, mlabel patterns and both axes</name>
  <files>dash.ado, dash_render.py, test/test_option_validation.py</files>
  <action><![CDATA[
    Make TR-06.1 (tokens and sentence, re-read on this tree; the dash_render.py comment is 06-05's), TR-06.2 (`axes` kind after the `int` branch; tokens :2995; `_seg_ya` as the max token and `_seg_yaxes_out`), TR-06.5 (`unab` splice in `_dash_mlabel_list`), TR-06.3 (define `_dash_axis_tokens` near `_dash_layer_axis_names` :1252 and add its copy-list entry after `"_dash_reference_lines",`; convert every `== "2"` yaxis/xaxis read listed), TR-06.4 (the multi-axis loop inside `_dash_add_glyph`, `_dash_assign_axis_ranges` called per pair there, its early return for a multi-token option (R1-04), one legend key), TR-06.7 maps. Edit test_option_validation.py's contract tokens with the comment (the count stays at the value read on this tree, 42 after S05, A33). Flip the pytest nodes of `<scratch>/s06/06-flips.txt` marked C10b (degree, yaxis) in place, HC1-16 included, with `Flipped:` lines. Append the block `* ==== S06 C10b: Parsed values ====` holding U06-01..U06-03 above `* ==== append new blocks above this line ====` in test/test_wp31_truth.cscript, in the form S01's Notes give (gate, timed `S06 start `/`S06 end ` display lines, `* ==== end S06 ====`; helpers `_u06_*` above the header; one block: C10b is the section's only measured row, A14), and U06-04 (with OV-51's flip and header line) in test_option_validation.cscript; append the C10b parity cases. Run both cscripts through the driver (`WP31_ONLY=S06`) and `python3 -m pytest test/test_lpoly_degree.py test/test_yaxis_both.py test/test_mlabel_patterns.py test/test_option_validation.py test/test_lpoly_rot.py test/test_axis2_suboptions.py test/test_help_claims_1.py test/test_statistical_helpers.py test/test_function_test_map.py test/test_mode_parity.py -k "not C18" -q -p no:cacheprovider`. Make TR-06.8's degree, mlabel, yaxis and lpoly help sentences (not scatteri's). TWOWAY_COVERAGE_AUDIT.md rows 94, 95 (degree above 3), 117 (`yaxis(1|2)`): append ` [WP-31 C10b: corrected -- degree 0-7; yaxis(1 2) draws the layer on both axes; mlabel() varlist elements]`. Close S01's "C10b" BUGS.md entry in BRIEF's form (functions _dash_validate_value kind axes, _dash_mlabel_list, _dash_axis_tokens, _dash_add_glyph, _dash_assign_axis_ranges; both renderers; pinned by test/test_yaxis_both.py::TestBothAxes::test_two_renderers, test/test_lpoly_degree.py::TestTheRule::test_degree_token_is_0_7, test/test_wp31_truth.cscript U06-03; fixture test/fixtures/parsed_values_truth.json; Residual, deferred (WP-31): degree above 7 is dash's bound; axes 3-9 are section 09); GAPS3 §9 C10b -> `- **C10b Tracked:** Closed in WP-31, BUGS.md "<S01's C10b title>", commit pending.` (A11; no amend). CHANGELOG: replace `<!-- WP-31 C10b -->` under `### Results that change` with `- lpoly and lpolyci accept degree(4) to degree(7) with Stata's rule-of-thumb bandwidth for each (degree above 3 was refused); an mlabel() element may be a varlist pattern such as t* or make-foreign, labelling the following y's (it was r(111)); yaxis(1 2) and xaxis(1 2) draw the layer on both axes as twoway does (refused before). (WP-31, C10b)` and under `### Fixed in WP-31` with `- degree(4-7), mlabel() patterns and yaxis(1 2) are accepted and drawn in both renderers. (WP-31, C10b)`; delete any `### Changed behaviour` C10b marker line (nothing is newly refused). Run `python3 -m pytest test/test_tracking_documents.py test/test_help_conformance.py -q -n0 -p no:cacheprovider`. Stage the C10b files (dash.ado, dash_render.py, dash.sthlp, TWOWAY_COVERAGE_AUDIT.md, BUGS.md, CHANGELOG.md, GAPS3.md, scripts/extract_parsed_values_truth.do, test/test_yaxis_both.py, test/test_lpoly_degree.py, test/test_mlabel_patterns.py, test/test_option_validation.py, test/test_wp31_truth.cscript, test/test_option_validation.cscript, test/test_mode_parity.py, test/function_test_map.py, the flipped files; `git add -f` the fixture; NOT test/test_scatteri_division.py), check names, write `<scratch>/s06/msg-c10b.txt`, grep for `claude|anthropic` (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c "degree=int,0,7" dash.ado` prints 1; `grep -c "yaxis=axes,1,2" dash.ado` prints 1; `grep -c '"_dash_axis_tokens",' dash_render.py` prints 1; `grep -c "U06-0[1-3] PASS" <scratch>/s06/run_test_wp31_truth.log` prints 3; `grep -c "U06-04 PASS\|OV-51 PASS" <scratch>/s06/run_test_option_validation.log` prints 2; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 C10b)`; `git show --name-only --format= HEAD | grep -c scatteri_division` prints 0; `grep -c "C10b Tracked:\*\* Closed in WP-31, BUGS.md \".*\", commit pending\.$" GAPS3.md` prints 1; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>degree 4-7 fitted with the live constants, mlabel() patterns expanded in place, and yaxis(1 2) drew each layer on both axes with one legend key in both renderers through moves; C10b was closed in one green commit.</done>
</task>

<task type="auto" id="06-04">
  <name>Evaluate scatteri p/p and close C18</name>
  <files>dash_parse.mata, test/test_parser.cscript, test/test_scatteri_division.py</files>
  <action><![CDATA[
    Re-run `python3 -m pytest test/test_scatteri_division.py -q -n0 -p no:cacheprovider -rf > <scratch>/s06/06-04.log 2>&1` on the tree 06-03 left and refresh `<scratch>/06-04-failure.txt`. Make TR-06.6 in dash_parse.mata (`_dash_imm_number` branch; header comment :1887-1893; header index entry). In test_parser.cscript remove `"scatteri 2/2 1"` from P1A-61's list (:737), rewrite the comment :728-731 ("2/2 is read as twoway reads it, a division drawing 1 (WP-31 C18); 1/2, a range of two values, is refused by twoway too"), and add U06-05 after P1A-61's block in the script's form (`_p1a_logrun`, `assert r(rc)`, the spec's `values` read from the JSON through `cert_file_has`), each rc compared with `capture noisily twoway scatteri ...` in the same run. Add TR-06.7's program_coverage_map.py tuple entry. Append the C18 parity case. Run test_parser.cscript through the driver and `python3 -m pytest test/test_scatteri_division.py test/test_immediate_values.py test/test_program_coverage_map.py test/test_mode_parity.py -k "scatteri" -q -n0 -p no:cacheprovider`. Make TR-06.8's scatteri help sentence. TWOWAY_COVERAGE_AUDIT.md row 69: append ` [WP-31 C18: corrected -- p/p is evaluated as twoway's division]`. Close S01's "C18" BUGS.md entry in BRIEF's form (function _dash_imm_number; pinned by test/test_scatteri_division.py::TestDivision::test_the_branch_exists, test/test_parser.cscript U06-05; fixture test/fixtures/parsed_values_truth.json; Residual, deferred (WP-31): the hexadecimal literal 1.0X+3ff stays refused); GAPS3 §9 C18 -> `- **C18 Tracked:** Closed in WP-31, BUGS.md "<S01's C18 title>", commit pending.` (A11; no amend). CHANGELOG: replace `<!-- WP-31 C18 -->` under `### Results that change` with `- scatteri reads a coordinate p/q with p equal to q as twoway does, a division drawing 1 (0/0 is missing); dash refused it. (WP-31, C18)` and under `### Fixed in WP-31` with `- scatteri's p/p coordinate is evaluated as twoway's. (WP-31, C18)`. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Stage the C18 files, write `<scratch>/s06/msg-c18.txt`, grep (0), commit, re-grep.
  ]]></action>
  <verify><![CDATA[`grep -c '"scatteri 2/2 1"' test/test_parser.cscript` prints 0; `grep -c "U06-05 PASS" <scratch>/s06/run_test_parser.log` prints 1 and `grep -c "P1A-61 PASS"` prints 1; the pytest run reports 0 failed; `git log -1 --format=%s` ends `(WP-31 C18)`; `grep -c "C18 Tracked:\*\* Closed in WP-31, BUGS.md \".*\", commit pending\.$" GAPS3.md` prints 1; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>scatteri evaluated p/p as twoway's division in the Mata reader, the parser certification accepted it and still refused 1/2, and C18 was closed in one green commit.</done>
</task>

<task type="auto" id="06-05">
  <name>Mark the constants live and close F4</name>
  <files>dash_render.py, test/test_lpoly_constants_live.py</files>
  <action><![CDATA[
    Create test/test_lpoly_constants_live.py (F4's own file, A14) with `TestTheComment::test_constants_are_live` (reads dash_render.py:483-485 and fails while the comment says "dormant") and `TestTheComment::test_every_row_is_reachable` (for each `(kernel, pe)` key of `_LPOLY_ROT_CONSTANTS`, `_default_lpoly_bwidth` with `degree = pe - 1` on a small frame reaches that key: monkeypatch the dict with a sentinel per key and assert each is read once). Run `python3 -m pytest test/test_lpoly_constants_live.py -q -n0 -p no:cacheprovider -rf > <scratch>/s06/06-05.log 2>&1` on the tree 06-04 left (red) and write `<scratch>/06-05-failure.txt`. Rewrite dash_render.py:483-485 per TR-06.1's comment text. Run `python3 -m pytest test/test_lpoly_constants_live.py test/test_lpoly_degree.py test/test_lpoly_rot.py -q -n0 -p no:cacheprovider`. Close S01's "F4" BUGS.md entry in BRIEF's form (function _default_lpoly_bwidth, constant _LPOLY_ROT_CONSTANTS; pinned by test/test_lpoly_constants_live.py::TestTheComment::test_every_row_is_reachable); GAPS3 §9 F4 -> `- **F4 Tracked:** Closed in WP-31, BUGS.md "<S01's F4 title>", commit pending.` (A11; no amend). CHANGELOG: replace `<!-- WP-31 F4 -->` under `### Fixed in WP-31` with `- The lpoly rule-of-thumb constants for degree 4-7 are reachable and tested. (WP-31, F4)`; delete any other F4 marker line. Run `python3 -m pytest test/test_tracking_documents.py -q -n0 -p no:cacheprovider`. Stage dash_render.py, test/test_lpoly_constants_live.py, BUGS.md, CHANGELOG.md, GAPS3.md; write `<scratch>/s06/msg-f4.txt`; grep (0); commit; re-grep. Hand-back note: whether `_DASH_AXIS_FINISH_JS` was edited (TR-06.3) and S09's inputs (`_seg_yaxes_out`, the `axes` kind, `_dash_axis_tokens`, the pair loop, the `_dash_assign_axis_ranges` early return).
  ]]></action>
  <verify><![CDATA[`grep -c "are dormant" dash_render.py` prints 0; `grep -c FAILED <scratch>/s06/06-05.log` is at least 1; the pytest runs report 0 failed; `git log -1 --format=%s` ends `(WP-31 F4)`; `grep -c '<!-- WP-31 \(C10b\|C18\|F4\) -->' CHANGELOG.md` prints 0; `grep -c "^- \*\*\(C10b\|C18\|F4\) Tracked:\*\* Closed in WP-31, BUGS.md \".*\", commit pending\.$" GAPS3.md` prints 3; `git log -1 --format=%B | grep -Eic 'claude|anthropic'` prints 0.]]></verify>
  <done>Every rule-of-thumb constant row was proved reachable by a test in F4's own file and the comment said so, and F4 was closed in one green commit, leaving three commits on wp31-s06 for the merger.</done>
</task>

## Section completion criteria

- `degree=int,0,7`; `axes` kind; `yaxis(1 2)` two renderers on two ranges in both modes through moves, one legend key; `mlabel()` elements `unab`'d; `scatteri p/p` drawn; the constants comment live and every row reachable by a test.
- U06-01..U06-05 PASS; OV-51, P1A-61, HC1-16 and the contract flipped with reasons; parity cases green; three commits; three BUGS entries closed; three GAPS3 lines rewritten with `commit pending`; markers replaced; five regression test files, one or more per row, none staged red by an earlier row's commit.

## Notes

- **Keep the two-axis loop inside `_dash_add_glyph`.** `_make_figure_body` and the served `_dash_draw_layer` are R12 hot functions with other batch owners; the loop and the per-pair `_dash_assign_axis_ranges` call must live in the shared helper so neither caller changes.
- **Every `== "2"` site.** grep `yaxis\|xaxis` in dash_render.py and dash_render's `_DASH_AXIS_FINISH_JS`; the test `test_no_equality_read_remains` is the guard. S09 extends the same token reads to "3".."9".
- **`unab` is the only expansion.** Never `fvunab` or `tsunab`: twoway's `MLabels(string)` uses `unab`.
- **Legend items are created lazily** (REVIEW-1 R1-27). `legend_label` makes a `LegendItem` when the glyph is added, so the later pairs' items are removed from `fig.legend[0].items` only after every pair has been drawn, never before; `TestBothAxes::test_one_legend_key[mode]` pins the one key. If a mapper-recognised flag that suppresses the label exists on this tree (grep `_dash_no_legend`), use it for the later pairs instead and record which in the docstring.
- **Mata declarations.** `k`, `a`, `b` must be declared at the top of `_dash_imm_number`; Mata refuses an undeclared name under `set matastrict on` (the file's header sets it: check).
- **python_exec hazard**: check `~/.stata19/console/stata19.rc` after each cscript run.
- **Shared files (R1-R13).** R1: the S06 block, one area case plus OV-51's flip, U06-05 in test_parser.cscript. R2: `_dash_axis_tokens` after `"_dash_reference_lines",`. R3: the degree/yaxis/mlabel/scatteri/lpoly sentences only. R4: C10b two markers, C18 two, F4 one (others deleted). R5: three entries. R6: no new program; `version 19` not needed; Mata header index updated. R7: one fixture for three rows. R8: four CORPUS, one MOVE_CORPUS. R9: flips recorded. R10: the contract count unchanged (tokens replaced one for one; 42 on the post-S05 tree, A33). R12: S06 is cut after S05 lands and then edits `_dash_option_rules` on the lines S05 left (A32); S06 edits `_dash_add_glyph`, not `_make_figure_body`/`_generate_app_source`; if `_DASH_AXIS_FINISH_JS` needs a token read, S06 is batch 2's only editor of it (R11's table has none for batch 2) -- state it in the hand-back.
- **For S09 (batch 3; `Depends on: 01, 06`, A32).** The `axes` kind's bounds become `1,9`; `_dash_axis_tokens` returns up to nine tokens; `_dash_add_glyph`'s pair loop already handles n tokens; `_dash_assign_axis_ranges`'s early return for multi-token options stays; the range names `y3`..`y9` are S09's.
- **For S19 (lpoly JS, batch 6).** `dash_lpoly` must carry the `pe` 5 and 7 constants.
